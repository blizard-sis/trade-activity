import json

from flask import Flask, send_from_directory

from .api import register_api
from .config import ROOT, load_config
from .storage import database

FRONTEND = ROOT / "frontend" / "dist"


def create_app():
    app = Flask(__name__, static_folder=str(FRONTEND), static_url_path="")
    app_config = load_config()
    app.config["TBANK_TOKEN"] = app_config.get("tbank_token", "")
    register_api(app)
    database.initialize()

    def frontend():
        return send_from_directory(FRONTEND, "index.html")

    routes = json.loads((ROOT / "routes.json").read_text(encoding="utf-8"))
    for route in routes:
        app.add_url_rule(route["path"], endpoint=route["id"], view_func=frontend)

    return app
