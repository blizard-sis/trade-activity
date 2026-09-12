import json

from flask import Blueprint, jsonify, request

from ..storage import database


settings_api = Blueprint("settings", __name__, url_prefix="/api")
MONTHLY_FILTERS_KEY = "monthly_filters"
MONTHLY_FILTER_FIELDS = {"account", "ticker_mode", "ticker", "month_from", "month_to"}
POSITION_TABLE_SETTINGS_KEY = "position_table_settings"
POSITION_COLUMNS = {
    "entry_at", "exit_at", "account", "instrument", "direction", "entry_quantity",
    "remaining", "entry_price", "exit_price", "gross_result", "commission", "net_result",
    "status", "order_count", "entry_note", "exit_note", "journal",
}


@settings_api.route("/monthly-filters", methods=["GET", "PUT", "DELETE"])
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


@settings_api.route("/position-table-settings", methods=["GET", "PUT", "DELETE"])
def position_table_settings():
    if request.method == "GET":
        saved = database.get_setting(POSITION_TABLE_SETTINGS_KEY)
        settings = json.loads(saved) if saved else {}
        if settings.get("visible_columns") and not settings.get("journal_column_supported"):
            settings["visible_columns"].append("journal")
        return jsonify(settings)

    if request.method == "DELETE":
        database.delete_setting(POSITION_TABLE_SETTINGS_KEY)
        return "", 204

    requested_columns = request.get_json().get("visible_columns", [])
    visible_columns = [column for column in requested_columns if column in POSITION_COLUMNS]
    settings = {"visible_columns": visible_columns, "journal_column_supported": True}
    database.save_setting(POSITION_TABLE_SETTINGS_KEY, json.dumps(settings))
    return jsonify(settings)
