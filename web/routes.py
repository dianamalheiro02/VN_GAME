"""
web/routes.py
"""

from flask import Blueprint, render_template, request, redirect, url_for
from web.save_manager import (
    get_or_create_player_id,
    has_save,
    load_save_meta,
    load_world,
    save_world,
    delete_save,
)
from story.nodes import NODES, KNOWLEDGE, resolve_text_blocks

bp = Blueprint("story", __name__)


# ---------------------------------------------------------------------------
# Landing — Continue or New Game
# ---------------------------------------------------------------------------

@bp.route("/", methods=["GET"])
def index():
    player_id = get_or_create_player_id()

    if has_save(player_id):
        meta = load_save_meta(player_id)
        return render_template("landing.html", meta=meta)

    # No save on disk — go straight to the beginning
    return redirect(url_for("story.story_node", node_id="intro"))


@bp.route("/continue", methods=["POST"])
def continue_game():
    player_id = get_or_create_player_id()
    _, current_node = load_world(player_id)
    return redirect(url_for("story.story_node", node_id=current_node))


@bp.route("/new_game", methods=["POST"])
def new_game():
    player_id = get_or_create_player_id()
    delete_save(player_id)
    return redirect(url_for("story.story_node", node_id="intro"))


# ---------------------------------------------------------------------------
# Debug panel
# ---------------------------------------------------------------------------

@bp.route("/debug")
def debug_panel():
    player_id = get_or_create_player_id()
    world, current_node = load_world(player_id)

    npc_affinities = {
        name: npc.evaluate_affinity(world.player)
        for name, npc in world.npcs.items()
    }

    known_display = [
        KNOWLEDGE.get(k, k)
        for k in world.player.knowledge
    ]

    return render_template(
        "partials/debug.html",
        world=world,
        current_node=current_node,
        ethics=vars(world.player.ethics),
        attributes=vars(world.player.attributes),
        npc_affinities=npc_affinities,
        known_display=known_display
    )


# ---------------------------------------------------------------------------
# Story nodes
# ---------------------------------------------------------------------------

@bp.route("/story/<node_id>", methods=["GET", "POST"])
def story_node(node_id):
    player_id = get_or_create_player_id()

    if node_id not in NODES:
        return f"Unknown node: '{node_id}'", 404

    world, _ = load_world(player_id)
    node = NODES[node_id]
    resolved_text = resolve_text_blocks(node, world)

    if request.method == "POST":
        choice_id = request.form.get("choice")
        if not choice_id or choice_id not in node.choices:
            return "Invalid choice.", 400

        choice = node.choices[choice_id]
        world.apply_effects(choice.effects)

        # Auto-save after every choice — next_node is where we resume
        save_world(player_id, world, current_node=choice.next_node)

        return redirect(url_for("story.story_node", node_id=choice.next_node))

    return render_template(
        node.template,
        node=node,
        text_blocks=resolved_text
    )
