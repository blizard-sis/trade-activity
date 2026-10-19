from flask import Flask, abort, send_from_directory
from werkzeug.exceptions import NotFound

from .api import register_api
from .config import ROOT, load_config
from .storage import database

FRONTEND = ROOT / "frontend" / "dist"


def create_app():
    app = Flask(__name__, static_folder=None)
    app_config = load_config()
    app.config["TBANK_TOKEN"] = app_config.get("tbank_token", "")
    register_api(app)
    database.initialize()

    @app.get("/")
    @app.get("/<path:path>")
    def frontend(path=""):
        if path == "api" or path.startswith("api/"):
            abort(404)
        if path:
            try:
                return send_from_directory(FRONTEND, path)
            except NotFound:
                # Missing assets must not receive HTML, even if they have no extension.
                if path == "assets" or path.startswith("assets/") or "." in path.rsplit("/", 1)[-1]:
                    raise
        # React owns page routing; the server only needs the built application.
        return send_from_directory(FRONTEND, "index.html")

    return app
