"""
web/save_manager.py

Disk-based save file system.

How it works:
- On first visit, a UUID is generated and stored in the browser cookie as `player_id`.
  This is the only thing that ever lives in the cookie.
- Every world state is serialised to  saves/<player_id>.json  after each choice.
- On return, the save file is loaded from disk if it exists.
- The session (flask_session, filesystem) is used as a fast in-memory cache
  for the current request cycle — the save file is the source of truth.

Save file format:
{
    "player_id":  "...",
    "saved_at":   "2025-01-01T12:00:00",
    "current_node": "greybrook_square",
    "world": { ...full world state dict... }
}
"""

import os
import json
import uuid
from datetime import datetime, timezone

from flask import session
from engine.world import WorldState, NPC, Player, Ethics, Attributes

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SAVES_DIR = os.path.join(os.path.dirname(__file__), "..", "saves")


def _ensure_saves_dir() -> None:
    os.makedirs(SAVES_DIR, exist_ok=True)


def _save_path(player_id: str) -> str:
    # Sanitise — player_id is a UUID so this is safe, but be explicit
    safe_id = "".join(c for c in player_id if c.isalnum() or c == "-")
    return os.path.join(SAVES_DIR, f"{safe_id}.json")


# ---------------------------------------------------------------------------
# Player identity
# ---------------------------------------------------------------------------

def get_or_create_player_id() -> str:
    """
    Return the player's UUID from the session cookie.
    Creates and stores one if this is a first visit.
    """
    if "player_id" not in session:
        session["player_id"] = str(uuid.uuid4())
    return session["player_id"]


# ---------------------------------------------------------------------------
# Default world factory
# ---------------------------------------------------------------------------

def _default_world_data() -> dict:
    return {
        "location": "Greybrook",
        "current_node": "intro",

        "player": {
            "name": "Adventurer",
            "ethics": {
                "compassion": 0,
                "authority": 0,
                "curiosity": 0
            },
            "attributes": {
                "intellect": 0,
                "resolve": 0,
                "presence": 0,
                "physique": 0
            },
            "knowledge": [],
            "scars": []
        },

        "curse_stage": 1,
        "instability": 0,
        "flags": [],

        "npcs": {
            "Mira": {
                "values": {"compassion": 1.5, "authority": -1.0, "curiosity": 0.5},
                "beliefs": {"king_failed_us": True, "magic_is_dangerous": True},
                "memory": [],
                "openness": 0.8,
                "suspicion": 1.2
            },
            "Elowen": {
                "values": {"compassion": 0.8, "authority": -0.5, "curiosity": 2.0},
                "beliefs": {"magic_is_alive": True, "curse_has_intent": True},
                "memory": [],
                "openness": 1.5,
                "suspicion": 0.5
            }
        }
    }


# ---------------------------------------------------------------------------
# Serialise / Deserialise WorldState
# ---------------------------------------------------------------------------

def _world_to_dict(world: WorldState, current_node: str) -> dict:
    return {
        "current_node": current_node,
        "location": world.location,

        "player": {
            "name": world.player.name,
            "ethics": vars(world.player.ethics),
            "attributes": vars(world.player.attributes),
            "knowledge": list(world.player.knowledge),
            "scars": world.player.scars
        },

        "curse_stage": world.curse_stage,
        "instability": world.instability,
        "flags": list(world.flags),

        "npcs": {
            name: {
                "values": npc.values,
                "beliefs": npc.beliefs,
                "memory": npc.memory,
                "openness": npc.openness,
                "suspicion": npc.suspicion
            }
            for name, npc in world.npcs.items()
        }
    }


def _dict_to_world(data: dict) -> WorldState:
    player = Player(
        name=data["player"]["name"],
        ethics=Ethics(**data["player"]["ethics"]),
        attributes=Attributes(**data["player"]["attributes"]),
        knowledge=set(data["player"]["knowledge"]),
        scars=data["player"]["scars"]
    )

    npcs = {
        name: NPC(
            name=name,
            values=info["values"],
            beliefs=info["beliefs"],
            memory=info.get("memory", []),
            openness=info.get("openness", 1.0),
            suspicion=info.get("suspicion", 1.0)
        )
        for name, info in data["npcs"].items()
    }

    return WorldState(
        location=data["location"],
        player=player,
        npcs=npcs,
        curse_stage=data["curse_stage"],
        instability=data.get("instability", 0),
        flags=set(data["flags"])
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def has_save(player_id: str) -> bool:
    """Return True if a save file exists for this player."""
    return os.path.exists(_save_path(player_id))


def load_save_meta(player_id: str) -> dict | None:
    """
    Return lightweight save metadata (no full world reconstruction)
    for the Continue screen: node name, timestamp, location.
    Returns None if no save exists.
    """
    path = _save_path(player_id)
    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    return {
        "saved_at":     raw.get("saved_at", "Unknown"),
        "current_node": raw["world"].get("current_node", "intro"),
        "location":     raw["world"].get("location", "Unknown"),
        "player_name":  raw["world"]["player"].get("name", "Adventurer")
    }


def load_world(player_id: str) -> tuple[WorldState, str]:
    """
    Load WorldState from disk (or create a fresh one).
    Returns (world, current_node).
    """
    _ensure_saves_dir()
    path = _save_path(player_id)

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        world_data = raw["world"]
    else:
        world_data = _default_world_data()

    current_node = world_data.get("current_node", "intro")
    world = _dict_to_world(world_data)
    return world, current_node


def save_world(player_id: str, world: WorldState, current_node: str) -> None:
    """
    Persist the world state to disk.
    Called automatically after every choice in routes.py.
    """
    _ensure_saves_dir()

    payload = {
        "player_id": player_id,
        "saved_at":  datetime.now(timezone.utc).isoformat(),
        "world":     _world_to_dict(world, current_node)
    }

    path = _save_path(player_id)
    # Write to a temp file first, then rename — avoids corrupt saves on crash
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp_path, path)


def delete_save(player_id: str) -> None:
    """Wipe the save file. Called on New Game."""
    path = _save_path(player_id)
    if os.path.exists(path):
        os.remove(path)
