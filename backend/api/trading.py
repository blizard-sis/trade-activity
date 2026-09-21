from datetime import datetime
import json

from flask import Blueprint, Response, current_app, jsonify, request

from ..domain.analytics import ticker_family
from ..storage import database
from ..services.reports import get_monthly_report
from ..services.journal import get_journal_positions
from ..services.export import build_export_document
from ..services.sync import sync_trades
from ..services.imports import import_tradingview_positions


trading_api = Blueprint("trading", __name__, url_prefix="/api")


@trading_api.post("/imports/tradingview")
def import_tradingview():
    request.max_content_length = 20 * 1024 * 1024
    files = request.files.getlist("files")
    if not files or len(files) > 6:
        return jsonify(error="Выберите от 1 до 6 CSV-файлов TradingView"), 400
    try:
        result = import_tradingview_positions(
            [(file.filename or "CSV", file.read()) for file in files],
            request.form.get("account_name", "Paper Trading"),
        )
    except ValueError as error:
        return jsonify(error=str(error)), 400
    return jsonify(result)



@trading_api.get("/accounts")
def accounts():
    return jsonify(database.get_accounts())


@trading_api.get("/tickers")
def tickers():
    values = database.get_tickers(request.args.getlist("account"))
    return jsonify(sorted({ticker_family(ticker) for ticker in values}))


@trading_api.get("/positions")
def positions():
    return jsonify(get_journal_positions(request.args))


@trading_api.get("/positions/export")
def export_positions():
    positions = get_journal_positions(request.args)
    document = build_export_document(positions, request.args)
    filename = f"trade-activity-{datetime.now().date().isoformat()}.json"
    return Response(
        json.dumps(document, ensure_ascii=False, indent=2),
        content_type="application/json; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@trading_api.get("/monthly")
def monthly():
    return jsonify(get_monthly_report(request.args))


@trading_api.post("/sync")
def sync():
    token = current_app.config.get("TBANK_TOKEN")
    if not token:
        return jsonify(error="Укажите tbank_token в config.json"), 400

    try:
        return jsonify(sync_trades(token))
    except Exception as error:
        return jsonify(error=str(error)), 502
