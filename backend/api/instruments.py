from flask import Blueprint, current_app, jsonify, request

from ..services import instruments as service
from ..storage import instruments as storage

instruments_api = Blueprint("instruments", __name__, url_prefix="/api/instruments")


@instruments_api.errorhandler(ValueError)
def invalid(error):
    return jsonify(error=str(error)), 400


@instruments_api.errorhandler(LookupError)
def missing(error):
    return jsonify(error=str(error)), 404


@instruments_api.errorhandler(RuntimeError)
def unavailable(error):
    return jsonify(error=str(error)), 502


@instruments_api.get("/search")
def search():
    return jsonify(
        service.search_instruments(current_app.config["TBANK_TOKEN"], request.args.get("q", ""))
    )


@instruments_api.post("/select")
def select():
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or not isinstance(body.get("kind"), str):
        raise ValueError("Выберите инструмент из результатов поиска")
    return jsonify(
        service.select_instrument(current_app.config["TBANK_TOKEN"], body.get("id"), body["kind"])
    )


@instruments_api.route("/links", methods=["GET", "POST"])
def links():
    if request.method == "GET":
        return jsonify(storage.get_links())
    return jsonify(service.save_link(request.get_json(silent=True))), 201


@instruments_api.route("/links/<link_id>", methods=["PUT", "DELETE"])
def link(link_id):
    if request.method == "DELETE":
        storage.delete_link(link_id)
        return "", 204
    return jsonify(service.save_link(request.get_json(silent=True), link_id))


@instruments_api.post("/links/<link_id>/refresh")
def refresh(link_id):
    return jsonify(service.refresh_link(current_app.config["TBANK_TOKEN"], link_id))
