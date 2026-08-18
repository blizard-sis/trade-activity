import json
from datetime import datetime, timezone

from flask import Blueprint, Response, current_app, jsonify, request

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
    return jsonify(_positions_with_notes(request.args))


@api.get("/positions/export")
def export_positions():
    positions = _positions_with_notes(request.args)
    document = {
        "format": "trade-activity",
        "version": 1,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "filters": {
            key: value
            for key, value in request.args.items()
            if key not in {"sort", "direction_sort"}
        },
        "summary": _export_summary(positions),
        "positions": [_export_position(position) for position in positions],
    }
    filename = f"trade-activity-{datetime.now().date().isoformat()}.json"
    return Response(
        json.dumps(document, ensure_ascii=False, indent=2),
        content_type="application/json; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _positions_with_notes(filters):
    positions = build_positions(database.get_trades(filters))
    positions = filter_positions(positions, filters)
    notes = database.get_position_notes([position["id"] for position in positions])
    for position in positions:
        position.update(notes.get(position["id"], {"entry_note": "", "exit_note": ""}))
    return positions


def _export_summary(positions):
    closed = [position for position in positions if position["status"] == "closed"]
    wins = sum(position["net_result"] > 0 for position in closed)
    losses = sum(position["net_result"] < 0 for position in closed)
    return {
        "positions": len(positions),
        "closed": len(closed),
        "open": len(positions) - len(closed),
        "wins": wins,
        "losses": losses,
        "breakeven": len(closed) - wins - losses,
        "win_rate_percent": wins / len(closed) * 100 if closed else 0,
        "gross_result_rub": sum(position["gross_result"] for position in closed),
        "commission_rub": sum(position["commission"] for position in closed),
        "net_result_rub": sum(position["net_result"] for position in closed),
    }


def _export_position(position):
    return {
        "account": position["account_name"],
        "ticker": position["ticker"],
        "instrument": position["instrument_name"],
        "direction": position["direction"],
        "status": position["status"],
        "entry_at": position["entry_at"],
        "exit_at": position["exit_at"],
        "entry_quantity": position["entry_quantity"],
        "exit_quantity": position["exit_quantity"],
        "remaining_quantity": position["remaining"],
        "entry_price": position["entry_price"],
        "exit_price": position["exit_price"],
        "price_unit": position["currency"],
        "gross_result_rub": position["gross_result"],
        "commission_rub": position["commission"],
        "net_result_rub": position["net_result"],
        "order_count": position["order_count"],
        "entry_note": position["entry_note"],
        "exit_note": position["exit_note"],
    }


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
