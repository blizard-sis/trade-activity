import json
from pathlib import Path

from flask import Flask, jsonify, render_template, request

import database
from positions import build_positions, filter_positions, monthly_report, ticker_family
from tbank import TBankClient, operation_trades


CONFIG_PATH = Path(__file__).with_name("config.json")
CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

app = Flask(__name__)
database.init_database()


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/monthly")
def monthly():
    return render_template("monthly.html")


@app.get("/api/accounts")
def get_accounts():
    return jsonify(database.accounts())


@app.get("/api/tickers")
def get_tickers():
    tickers = database.tickers(request.args.get("account"))
    return jsonify(sorted({ticker_family(ticker) for ticker in tickers}))


@app.route("/api/monthly-filters", methods=["GET", "PUT", "DELETE"])
def monthly_filters():
    if request.method == "GET":
        saved = database.get_setting("monthly_filters")
        return jsonify(json.loads(saved) if saved else {})
    if request.method == "DELETE":
        database.delete_setting("monthly_filters")
        return "", 204

    allowed = {"account", "ticker_mode", "ticker", "month_from", "month_to"}
    filters = {key: value for key, value in request.get_json().items() if key in allowed}
    database.save_setting("monthly_filters", json.dumps(filters))
    return jsonify(filters)


@app.get("/api/trades")
def get_trades():
    trades = database.load_trades(request.args)
    positions = build_positions(trades)
    return jsonify(filter_positions(positions, request.args))


@app.get("/api/monthly")
def get_monthly_report():
    trades = database.load_trades(request.args)
    return jsonify(monthly_report(build_positions(trades), request.args))


@app.post("/api/sync")
def sync():
    token = CONFIG.get("tbank_token")
    if not token:
        return jsonify(error="Укажите tbank_token в файле config.json"), 400

    try:
        client = TBankClient(token)
        known_instruments = database.instruments()
        saved = 0

        for account in client.accounts():
            database.save_account(account)
            trades = []

            for operation in client.operations(account["id"]):
                uid = operation.get("instrumentUid", "")
                if uid not in known_instruments:
                    known_instruments[uid] = client.instrument(uid) if uid else {}
                trades.extend(operation_trades(account["id"], operation, known_instruments[uid]))

            saved += database.save_trades(trades)

        return jsonify(saved=saved)
    except Exception as error:
        return jsonify(error=str(error)), 502


if __name__ == "__main__":
    app.run(port=CONFIG.get("port", 8000), debug=True)
