# The Cursed Kingdom

A narrative RPG engine built with Python and Flask. The player travels to a cursed kingdom at the king's demand, making choices that shape their ethics, attributes, and relationships with the world around them. Every decision is remembered by the engine, and by the people you meet.

Built as a portfolio project to demonstrate data-driven content pipelines, emergent NPC behaviour, and clean separation between story content and game logic.

---

## Features

- **Visual novel presentation**: fullscreen scene backgrounds, typewriter text delivery, click or keypress to advance
- **Branching narrative**: choices drive ethics and attribute stats; past decisions change what text appears in future scenes
- **Emergent NPC affinity**: NPCs evaluate how much they like you based on your ethical alignment with their values and what they remember you doing, not a simple points counter
- **YAML-driven content**: all story prose, choices, and effects live in plain YAML files; no Python required to write new scenes
- **Persistent save system**: auto-saves to disk after every choice; return to your exact last checkpoint from any device session
- **Knowledge registry**: tracks what the player has learned using short identifier keys mapped to readable journal entries
- **Debug panel**: live view of all world state, NPC memory, ethics, attributes, affinity scores, and flags; radar chart for player attributes

---

## Project Structure

```
GAME/
├── app.py                        # Flask application factory
├── engine/
│   └── world.py                  # Core data classes: Player, NPC, WorldState, Ethics, Attributes
├── story/
│   ├── nodes.py                  # Content loader and text resolution engine
│   └── content/
│       ├── knowledge.yaml        # Knowledge key → display text registry
│       ├── intro.yaml
│       ├── greybrook_square.yaml
│       ├── joseph_aftermath.yaml
│       └── ...                   # One .yaml file per scene
├── web/
│   ├── routes.py                 # Flask routes: landing, story nodes, debug panel
│   ├── save_manager.py           # Disk-based save system (per-player UUID)
│   └── state.py                  # Session helpers
├── static/
│   └── style.css                 # All styles in painterly fantasy aesthetic
└── templates/
    ├── base.html
    ├── landing.html
    ├── partials/
    │   └── debug.html
    └── story/
        ├── vn_scene.html         # Shared VN template (all scenes extend this)
        ├── intro.html
        ├── greybrook_square.html
        └── ...
```

---

## How the Engine Works

### Content Pipeline

Story content lives entirely in YAML, separate from Python logic. A scene file looks like this:

```yaml
id: greybrook_square
template: story/greybrook_square.html

text_blocks:
  - "By the time you reach the village of Greybrook, dusk is already settling in."
  - condition: mira_memory_showed_empathy
    text:
      - "Mira glances at you differently now."

choices:
  comfort:
    text: "Kneel and comfort her"
    effects:
      ethics.compassion: 2
      attr.presence: 1
      event: showed_empathy
      knowledge: joseph_died_comforted
    next_node: joseph_aftermath
```

To write a new scene: create a `.yaml` file in `story/content/`. No Python changes required.

### NPC Affinity

Affinity is emergent, it is never set directly. Each NPC holds a set of ethical values they care about (e.g. Mira weights compassion highly, distrusts authority). The engine computes affinity at runtime by:

1. Multiplying each of the player's ethics scores by the NPC's weight for that value
2. Applying memory modifiers. Events the NPC witnessed (like `showed_empathy` or `invoked_authority`) add or subtract from the score, scaled by the NPC's `openness` and `suspicion` personality traits

The same player ethics score can produce different affinity with different NPCs, because they care about different things.

### Effects System

Choice effects use a dotted key format resolved by an `EffectKind` enum:

| Key format | Effect |
|---|---|
| `ethics.compassion: 2` | Adds 2 to player compassion |
| `attr.resolve: -1` | Subtracts 1 from player resolve |
| `event: showed_empathy` | Appends to all NPC memory logs |
| `belief.Mira.king_failed_us: false` | Changes a specific NPC belief |
| `knowledge: joseph_died_comforted` | Adds a knowledge entry to the player |
| `curse: 1` | Increments global curse stage |
| `location: Capital` | Updates the world location |

### Save System

Each player is assigned a UUID on first visit, stored in a lightweight server-side session. The full world state serialises to `saves/<uuid>.json` after every choice. On return, the engine reads the last saved node and resumes there.

Saves are written atomically, the engine writes to a `.tmp` file first, then renames it, so a crash mid-write never corrupts the save file.

---

## Setup

**Requirements:** Python 3.11+

```bash
# Install dependencies
pip install flask flask-session pyyaml

# Run
python app.py
```

Then open `http://localhost:5000` or `http://127.0.0.1:5000` in your browser.

**Add to `.gitignore`:**
```
saves/
.flask_sessions/
```

---

## Adding a New Scene

1. Create `story/content/your_scene.yaml` with `id`, `template`, `text_blocks`, and `choices`
2. Create `templates/story/your_scene.html`:
   ```jinja
   {% extends "story/vn_scene.html" %}
   {% set bg_image = "your_background.png" %}
   ```
3. Add your background image to `static/`
4. If your scene uses conditional text, register the condition lambda in the `CONDITIONS` dict in `story/nodes.py`
5. Add any new knowledge keys to `story/content/knowledge.yaml`

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, Flask |
| Templating | Jinja2 |
| Session storage | Flask-Session (filesystem) |
| Content format | YAML |
| Frontend | Vanilla JS, CSS custom properties |
| Fonts | Cinzel, EB Garamond (Google Fonts) |

---

## Roadmap

- [ ] Journal UI: surface the knowledge registry in-game for the player
- [ ] NPC affinity indicators: subtle visual cues in dialogue based on relationship score
- [ ] Act 2 content: the capital, the king, Elowen's arc
- [ ] Deployment: hosted live demo (Render / Railway)

