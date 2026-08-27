"""
engine/world.py
"""

from dataclasses import dataclass, field
from enum import Enum


# ---------------------------------------------------------------------------
# Effect key parsing
# ---------------------------------------------------------------------------

class EffectKind(Enum):
    ETHICS     = "ethics"
    ATTRIBUTE  = "attr"
    EVENT      = "event"
    BELIEF     = "belief"
    KNOWLEDGE  = "knowledge"
    CURSE      = "curse"
    INSTABILITY = "instability"
    LOCATION   = "location"
    FLAG       = "flag"   # fallback: anything unrecognised becomes a flag


def _parse_effect_key(key: str) -> tuple[EffectKind, list[str]]:
    """
    Turn a dotted effect key into (kind, parts).

    Examples:
        "ethics.compassion"        -> (ETHICS,     ["compassion"])
        "attr.resolve"             -> (ATTRIBUTE,  ["resolve"])
        "belief.Mira.king_failed_us" -> (BELIEF,   ["Mira", "king_failed_us"])
        "event"                    -> (EVENT,       [])
        "knowledge"                -> (KNOWLEDGE,   [])
        "curse"                    -> (CURSE,        [])
        "instability"              -> (INSTABILITY,  [])
        "location"                 -> (LOCATION,     [])
        "anything_else"            -> (FLAG,         [])
    """
    prefix, *parts = key.split(".")

    kind_map = {k.value: k for k in EffectKind if k != EffectKind.FLAG}
    kind = kind_map.get(prefix, EffectKind.FLAG)
    return kind, parts


# ---------------------------------------------------------------------------
# Player stats
# ---------------------------------------------------------------------------

@dataclass
class Ethics:
    compassion: int = 0     # empathy, mercy, care
    authority:  int = 0     # respect for hierarchy / power
    curiosity:  int = 0     # desire to know, investigate, risk


@dataclass
class Attributes:
    intellect: int = 0      # reasoning, magic theory, analysis
    resolve:   int = 0      # mental endurance, willpower
    presence:  int = 0      # social influence, composure
    physique:  int = 0      # endurance, physical capability


@dataclass
class Player:
    name:       str
    ethics:     Ethics     = field(default_factory=Ethics)
    attributes: Attributes = field(default_factory=Attributes)
    knowledge:  set        = field(default_factory=set)
    scars:      list       = field(default_factory=list)


# ---------------------------------------------------------------------------
# NPC
# ---------------------------------------------------------------------------

@dataclass
class NPC:
    name: str

    values:   dict = field(default_factory=dict)   # ethical weights
    beliefs:  dict = field(default_factory=dict)   # what this NPC thinks is true
    memory:   list = field(default_factory=list)   # remembered player actions

    openness:   float = 1.0   # willingness to reconsider beliefs
    suspicion:  float = 1.0   # distrust baseline

    def evaluate_affinity(self, player: Player) -> float:
        """
        Emergent affinity score:
        ethics alignment with player + memory modifiers.
        """
        score = 0.0

        for value, weight in self.values.items():
            score += weight * getattr(player.ethics, value, 0)

        for event in self.memory:
            if event in ("showed_empathy", "long_stay"):
                score += 1.0 * self.openness
            elif event in ("invoked_authority", "short_stay"):
                score -= 1.0 * self.suspicion

        return round(score, 2)


# ---------------------------------------------------------------------------
# World state
# ---------------------------------------------------------------------------

@dataclass
class WorldState:
    location:    str    = ""
    player:      Player = field(default_factory=lambda: Player(name="Unknown"))
    npcs:        dict   = field(default_factory=dict)

    curse_stage: int = 0
    instability: int = 0
    flags:       set = field(default_factory=set)

    def apply_effects(self, effects: dict) -> None:
        """
        Apply narrative consequences from a choice's effects dict.
        Uses EffectKind enum instead of raw string splitting,
        so belief keys with dots in their names are safe.
        """
        for key, value in effects.items():
            kind, parts = _parse_effect_key(key)

            if kind == EffectKind.ETHICS:
                attr = parts[0]
                current = getattr(self.player.ethics, attr, None)
                if current is None:
                    raise AttributeError(f"Ethics has no attribute '{attr}'")
                setattr(self.player.ethics, attr, current + value)

            elif kind == EffectKind.ATTRIBUTE:
                attr = parts[0]
                current = getattr(self.player.attributes, attr, None)
                if current is None:
                    raise AttributeError(f"Attributes has no attribute '{attr}'")
                setattr(self.player.attributes, attr, current + value)

            elif kind == EffectKind.EVENT:
                for npc in self.npcs.values():
                    npc.memory.append(value)

            elif kind == EffectKind.BELIEF:
                if len(parts) != 2:
                    raise ValueError(
                        f"Belief effect key must be 'belief.<npc_name>.<belief_key>', got '{key}'"
                    )
                npc_name, belief_key = parts
                if npc_name not in self.npcs:
                    raise KeyError(f"No NPC named '{npc_name}'")
                self.npcs[npc_name].beliefs[belief_key] = value

            elif kind == EffectKind.KNOWLEDGE:
                self.player.knowledge.add(value)

            elif kind == EffectKind.CURSE:
                self.curse_stage += value

            elif kind == EffectKind.INSTABILITY:
                self.instability += value

            elif kind == EffectKind.LOCATION:
                self.location = value

            elif kind == EffectKind.FLAG:
                self.flags.add(key)
