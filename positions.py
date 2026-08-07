from itertools import groupby
import re


FUTURES_TICKER = re.compile(r"^(.+)[FGHJKMNQUVXZ]\d$")


def ticker_family(ticker):
    match = FUTURES_TICKER.match(ticker)
    return match.group(1) if match else ticker


def price_precision(price):
    text = f"{price:.9f}".rstrip("0").rstrip(".")
    return len(text.split(".")[1]) if "." in text else 0


def build_positions(trades):
    key = lambda trade: (trade["account_id"], trade["instrument_uid"])
    trades = sorted(trades, key=lambda trade: (*key(trade), trade["executed_at"], trade["trade_id"]))
    positions = []

    for _, instrument_trades in groupby(trades, key=key):
        current = None

        for trade in instrument_trades:
            quantity = trade["quantity"]
            commission_per_unit = abs(trade["commission"]) / quantity if quantity else 0
            payment_per_unit = trade["payment"] / quantity if quantity else 0

            while quantity:
                if current is None:
                    current = start_position(trade, quantity, commission_per_unit, payment_per_unit)
                    quantity = 0
                    continue

                same_direction = trade["side"] == current["entry_side"]
                if same_direction:
                    add_entry(current, trade, quantity, commission_per_unit, payment_per_unit)
                    quantity = 0
                    continue

                closed_quantity = min(quantity, current["remaining"])
                add_exit(current, trade, closed_quantity, commission_per_unit, payment_per_unit)
                quantity -= closed_quantity

                if current["remaining"] == 0:
                    positions.append(finish_position(current, "closed"))
                    current = None

        if current:
            positions.append(finish_position(current, "open"))

    return positions


def start_position(trade, quantity, commission_per_unit, payment_per_unit):
    return {
        "account_id": trade["account_id"],
        "account_name": trade["account_name"],
        "instrument_uid": trade["instrument_uid"],
        "ticker": trade["ticker"],
        "instrument_name": trade["instrument_name"],
        "direction": "long" if trade["side"] == "buy" else "short",
        "entry_side": trade["side"],
        "entry_at": trade["executed_at"],
        "exit_at": None,
        "entry_quantity": quantity,
        "exit_quantity": 0,
        "remaining": quantity,
        "entry_value": trade["price"] * quantity,
        "exit_value": 0,
        "currency": trade["currency"],
        "price_precision": price_precision(trade["price"]),
        "commission": commission_per_unit * quantity,
        "commission_currency": trade["commission_currency"],
        "cash_flow": payment_per_unit * quantity,
        "result_currency": trade["payment_currency"],
        "orders": {trade["operation_id"]},
    }


def add_entry(position, trade, quantity, commission_per_unit, payment_per_unit):
    position["entry_quantity"] += quantity
    position["remaining"] += quantity
    position["entry_value"] += trade["price"] * quantity
    position["commission"] += commission_per_unit * quantity
    position["cash_flow"] += payment_per_unit * quantity
    position["orders"].add(trade["operation_id"])
    position["price_precision"] = max(position["price_precision"], price_precision(trade["price"]))


def add_exit(position, trade, quantity, commission_per_unit, payment_per_unit):
    position["exit_quantity"] += quantity
    position["remaining"] -= quantity
    position["exit_value"] += trade["price"] * quantity
    position["exit_at"] = trade["executed_at"]
    position["commission"] += commission_per_unit * quantity
    position["cash_flow"] += payment_per_unit * quantity
    position["orders"].add(trade["operation_id"])
    position["price_precision"] = max(position["price_precision"], price_precision(trade["price"]))


def finish_position(position, status):
    position["status"] = status
    position["entry_price"] = position["entry_value"] / position["entry_quantity"]
    position["exit_price"] = (
        position["exit_value"] / position["exit_quantity"] if position["exit_quantity"] else None
    )
    position["order_count"] = len(position.pop("orders"))
    position["gross_result"] = position["cash_flow"] if status == "closed" else None
    position["net_result"] = (
        position["cash_flow"] - position["commission"] if status == "closed" else None
    )
    del position["cash_flow"]
    del position["entry_side"], position["entry_value"], position["exit_value"]
    return position


def filter_positions(positions, filters):
    if filters.get("direction"):
        positions = [item for item in positions if item["direction"] == filters["direction"]]
    if filters.get("status"):
        positions = [item for item in positions if item["status"] == filters["status"]]
    if filters.get("from"):
        positions = [item for item in positions if item["entry_at"] >= filters["from"]]
    if filters.get("to"):
        positions = [item for item in positions if item["entry_at"][:10] <= filters["to"]]

    sort_fields = {
        "date": "entry_at",
        "exit": "exit_at",
        "account": "account_name",
        "ticker": "ticker",
        "direction": "direction",
        "quantity": "entry_quantity",
        "entry": "entry_price",
        "status": "status",
    }
    field = sort_fields.get(filters.get("sort"), "entry_at")
    reverse = filters.get("direction_sort") != "asc"
    return sorted(positions, key=lambda item: (item[field] is not None, item[field]), reverse=reverse)


def monthly_report(positions, filters=None):
    filters = filters or {}
    ticker = filters.get("ticker")
    ticker_mode = filters.get("ticker_mode")
    if ticker and ticker_mode == "only":
        positions = [position for position in positions if ticker_family(position["ticker"]) == ticker]
    if ticker and ticker_mode == "exclude":
        positions = [position for position in positions if ticker_family(position["ticker"]) != ticker]

    months = {}

    for position in positions:
        if position["status"] != "closed":
            continue

        month = position["exit_at"][:7]
        if filters.get("month_from") and month < filters["month_from"]:
            continue
        if filters.get("month_to") and month > filters["month_to"]:
            continue

        row = months.setdefault(month, {
            "month": month,
            "positions": 0,
            "wins": 0,
            "losses": 0,
            "gross_result": 0,
            "commission": 0,
            "net_result": 0,
        })
        row["positions"] += 1
        row["gross_result"] += position["gross_result"]
        row["commission"] += position["commission"]
        row["net_result"] += position["net_result"]
        row["wins"] += position["net_result"] > 0
        row["losses"] += position["net_result"] < 0

    for row in months.values():
        row["win_rate"] = row["wins"] / row["positions"] * 100

    return sorted(months.values(), key=lambda row: row["month"], reverse=True)
