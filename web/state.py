"""
web/state.py

Game state persistence via flask_session (filesystem-backed).

WHY NOT session[]: Flask's default session is cookie-based and caps at ~4KB.
A growing world state will silently corrupt or get dropped. flask_session
stores data server-side and only puts a session ID in the cookie.

Setup: pip install Flask-Session
The session directory is created automatically on first run.
"""

from flask import session
from engine.world import WorldState, NPC, Player, Ethics, Attributes

# ---------------------------------------------------------------------------
# Default world factory
# ---------------------------------------------------------------------------

def _default_world_data() -> dict:
    return {
        "location": "Greybrook",

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
                "values": {
                    "compassion": 1.5,
                    "authority": -1.0,
                    "curiosity": 0.5
                },
                "beliefs": {
                    "king_failed_us": True,
                    "magic_is_dangerous": True
                },
                "memory": [],
                "openness": 0.8,
                "suspicion": 1.2
            },
            "Elowen": {
                "values": {
                    "compassion": 0.8,
                    "authority": -0.5,
                    "curiosity": 2.0
                },
                "beliefs": {
                    "magic_is_alive": True,
                    "curse_has_intent": True
                },
                "memory": [],
                "openness": 1.5,
                "suspicion": 0.5
            }
        }
    }


# ---------------------------------------------------------------------------
# Load / Save
# ---------------------------------------------------------------------------

def load_world() -> WorldState:
    if "world" not in session:
        session["world"] = _default_world_data()

    data = session["world"]

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


def save_world(world: WorldState) -> None:
    session["world"] = {
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


def reset_world() -> None:
    """Clear session state entirely — useful for a 'New Game' button."""
    session.pop("world", None)
