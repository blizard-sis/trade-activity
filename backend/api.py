import json

from flask import Blueprint, current_app, jsonify, request

from . import database
from .analytics import build_positions, filter_positions, monthly_report, ticker_family
from .sync import sync_trades


api = Blueprint("api", __name__, url_prefix="/api")
MONTHLY_FILTERS_KEY = "monthly_filters"
MONTHLY_FILTER_FIELDS = {"account", "ticker_mode", "ticker", "month_from", "month_to"}
POSITION_TABLE_SETTINGS_KEY = "position_table_settings"
POSITION_COLUMNS = {
    "entry_at", "exit_at", "account", "instrument", "direction", "entry_quantity",
    "remaining", "entry_price", "exit_price", "gross_result", "commission", "net_result",
    "status", "order_count", "entry_note", "exit_note",
}


@api.get("/accounts")
def accounts():
    return jsonify(database.get_accounts())


@api.get("/tickers")
def tickers():
    values = database.get_tickers(request.args.get("account"))
    return jsonify(sorted({ticker_family(ticker) for ticker in values}))


@api.route("/monthly-filters", methods=["GET", "PUT", "DELETE"])
def monthly_filters():
    if request.method == "GET":
        saved = database.get_setting(MONTHLY_FILTERS_KEY)
        return jsonify(json.loads(saved) if saved else {})

    if request.method == "DELETE":
        database.delete_setting(MONTHLY_FILTERS_KEY)
        return "", 204

    filters = {
        key: value
        for key, value in request.get_json().items()
        if key in MONTHLY_FILTER_FIELDS
    }
    database.save_setting(MONTHLY_FILTERS_KEY, json.dumps(filters))
    return jsonify(filters)


@api.route("/position-table-settings", methods=["GET", "PUT", "DELETE"])
def position_table_settings():
    if request.method == "GET":
        saved = database.get_setting(POSITION_TABLE_SETTINGS_KEY)
        return jsonify(json.loads(saved) if saved else {})

    if request.method == "DELETE":
        database.delete_setting(POSITION_TABLE_SETTINGS_KEY)
        return "", 204

    requested_columns = request.get_json().get("visible_columns", [])
    visible_columns = [column for column in requested_columns if column in POSITION_COLUMNS]
    settings = {"visible_columns": visible_columns}
    database.save_setting(POSITION_TABLE_SETTINGS_KEY, json.dumps(settings))
    return jsonify(settings)


@api.get("/positions")
def positions():
    positions = build_positions(database.get_trades(request.args))
    positions = filter_positions(positions, request.args)
    notes = database.get_position_notes([position["id"] for position in positions])
    for position in positions:
        position.update(notes.get(position["id"], {"entry_note": "", "exit_note": ""}))
    return jsonify(positions)


@api.put("/positions/<path:position_id>/notes")
def position_notes(position_id):
    notes = request.get_json()
    database.save_position_notes(
        position_id,
        notes.get("entry_note", ""),
        notes.get("exit_note", ""),
    )
    return jsonify(entry_note=notes.get("entry_note", ""), exit_note=notes.get("exit_note", ""))


@api.get("/monthly")
def monthly():
    positions = build_positions(database.get_trades(request.args))
    return jsonify(monthly_report(positions, request.args))


@api.post("/sync")
def sync():
    token = current_app.config.get("TBANK_TOKEN")
    if not token:
        return jsonify(error="Укажите tbank_token в config.json"), 400

    try:
        return jsonify(saved=sync_trades(token))
    except Exception as error:
        return jsonify(error=str(error)), 502
