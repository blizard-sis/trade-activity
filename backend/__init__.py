from flask import Flask, send_from_directory

from .storage import database
from .api import register_api
from .config import ROOT, load_config


FRONTEND = ROOT / "frontend" / "dist"


def create_app():
    app = Flask(__name__, static_folder=str(FRONTEND), static_url_path="")
    app_config = load_config()
    app.config["TBANK_TOKEN"] = app_config.get("tbank_token", "")
    register_api(app)
    database.initialize()

    @app.get("/")
    @app.get("/monthly")
    @app.get("/journal")
    def frontend():
        return send_from_directory(FRONTEND, "index.html")

    return app
