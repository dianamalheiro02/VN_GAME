"""
app.py

Flask application factory.

Session storage (flask_session, filesystem) is used only to persist the
player's UUID across requests. The full world state lives in saves/<uuid>.json,
written to disk after every choice by save_manager.py.

Install: pip install Flask-Session
"""

import os
from flask import Flask
from flask_session import Session
from web.routes import bp as story_bp


def create_app():
    app = Flask(__name__)

    # Secret key — swap for os.urandom(24) bytes in production
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

    # Session only stores player_id — tiny, safe for filesystem sessions
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_FILE_DIR"] = os.path.join(app.root_path, ".flask_sessions")
    app.config["SESSION_PERMANENT"] = False

    Session(app)

    app.register_blueprint(story_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
