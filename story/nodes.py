"""
story/nodes.py

Pure engine logic. No prose lives here.
All story content is loaded from story/content/*.yaml at startup.

Condition keys used in YAML map to named lambdas in CONDITIONS below.
To add a new condition: define it here, then reference it by name in your YAML.
"""

import os
import yaml
from dataclasses import dataclass
from typing import Callable
from engine.world import WorldState

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ConditionalText:
    condition: Callable     # (world: WorldState) -> bool
    text: list[str]


@dataclass
class Choice:
    text: str
    effects: dict
    next_node: str


@dataclass
class StoryNode:
    id: str
    template: str
    text_blocks: list       # list[str | ConditionalText]
    choices: dict           # { choice_id: Choice }


# ---------------------------------------------------------------------------
# Named conditions
# Map YAML condition keys to callable lambdas.
# Add new conditions here as your story grows.
# ---------------------------------------------------------------------------

CONDITIONS: dict[str, Callable[[WorldState], bool]] = {
    "mira_memory_showed_empathy":      lambda w: "showed_empathy"      in w.npcs["Mira"].memory,
    "mira_memory_pressed_for_answers": lambda w: "pressed_for_answers" in w.npcs["Mira"].memory,
    "mira_memory_invoked_authority":   lambda w: "invoked_authority"   in w.npcs["Mira"].memory,
    "mira_memory_short_stay":          lambda w: "short_stay"          in w.npcs["Mira"].memory,
    "mira_memory_long_stay":           lambda w: "long_stay"           in w.npcs["Mira"].memory,
    "mira_affinity_positive":          lambda w: w.npcs["Mira"].evaluate_affinity(w.player) >= 0,
    "mira_affinity_negative":          lambda w: w.npcs["Mira"].evaluate_affinity(w.player) < 0,
    "player_knows_shrine":             lambda w: "shrine_called_to_you" in w.player.knowledge,
    "curse_stage_high":                lambda w: w.curse_stage >= 3,
    
    "elowen_memory_listened":           lambda w: "listened_elowen"     in w.npcs["Elowen"].memory,
    "elowen_memory_pressed_for_answers":lambda w: "questioned_elowen"   in w.npcs["Elowen"].memory,
    "elowen_memory_left":               lambda w: "fled_shrine"         in w.npcs["Elowen"].memory,
    
    "elowen_memory_magic":              lambda w: "elowen_magic"        in w.npcs["Elowen"].memory,
    "elowen_memory_curse":              lambda w: "elowen_curse"        in w.npcs["Elowen"].memory,
    "elowen_memory_letter":             lambda w: "elowen_king"         in w.npcs["Elowen"].memory,        
}


# ---------------------------------------------------------------------------
# YAML loader
# ---------------------------------------------------------------------------

def _load_text_blocks(raw_blocks: list) -> list:
    """Convert raw YAML text_blocks into str | ConditionalText."""
    result = []
    for block in raw_blocks:
        if isinstance(block, str):
            result.append(block)
        elif isinstance(block, dict):
            condition_key = block.get("condition")
            if condition_key not in CONDITIONS:
                raise ValueError(
                    f"Unknown condition key '{condition_key}'. "
                    f"Register it in nodes.py CONDITIONS dict."
                )
            result.append(ConditionalText(
                condition=CONDITIONS[condition_key],
                text=block.get("text", [])
            ))
        else:
            raise TypeError(f"Unexpected text_block type: {type(block)}")
    return result


def _load_choices(raw_choices: dict) -> dict:
    """Convert raw YAML choices into Choice objects."""
    return {
        choice_id: Choice(
            text=data["text"],
            effects=data.get("effects") or {},
            next_node=data["next_node"]
        )
        for choice_id, data in raw_choices.items()
    }


def _load_node_from_yaml(path: str) -> StoryNode:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return StoryNode(
        id=data["id"],
        template=data["template"],
        text_blocks=_load_text_blocks(data.get("text_blocks", [])),
        choices=_load_choices(data.get("choices", {}))
    )


def load_all_nodes(content_dir: str) -> dict[str, StoryNode]:
    """Load every *.yaml file in content_dir as a StoryNode."""
    nodes = {}
    for filename in os.listdir(content_dir):
        if filename.endswith(".yaml") and filename != "knowledge.yaml":
            path = os.path.join(content_dir, filename)
            node = _load_node_from_yaml(path)
            nodes[node.id] = node
    return nodes


# ---------------------------------------------------------------------------
# Knowledge registry
# ---------------------------------------------------------------------------

def load_knowledge_registry(content_dir: str) -> dict[str, str]:
    """Load knowledge key -> display text mapping."""
    path = os.path.join(content_dir, "knowledge.yaml")
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ---------------------------------------------------------------------------
# Module-level singletons (loaded once at startup)
# ---------------------------------------------------------------------------

_CONTENT_DIR = os.path.join(os.path.dirname(__file__), "content")

NODES: dict[str, StoryNode] = load_all_nodes(_CONTENT_DIR)
KNOWLEDGE: dict[str, str] = load_knowledge_registry(_CONTENT_DIR)


# ---------------------------------------------------------------------------
# Text resolution
# ---------------------------------------------------------------------------

def resolve_text_blocks(node: StoryNode, world: WorldState) -> list[str]:
    resolved = []
    for block in node.text_blocks:
        if isinstance(block, str):
            resolved.append(block)
        elif isinstance(block, ConditionalText):
            try:
                if block.condition(world):
                    resolved.extend(block.text)
            except Exception as e:
                print(f"[TEXT CONDITION ERROR] {e}")
    return resolved
