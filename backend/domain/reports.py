from .analytics import ticker_family
from .winrate import exit_category, win_rates


def trading_report(positions, filters):
    period_length = 10 if filters.get("group_by") == "day" else 7
    positions = _filter_report_positions(positions, filters, period_length)
    periods = {}

    for position in positions:
        period = position["exit_at"][:period_length]
        currency = (position["result_currency"] or "rub").upper()
        row = periods.setdefault(
            (period, currency),
            {
                "period": period,
                "currency": currency,
                "positions": 0,
                "wins": 0,
                "losses": 0,
                "takes": 0,
                "stops": 0,
                "manual": 0,
                "mixed": 0,
                "unknown": 0,
                "gross_result": 0,
                "commission": 0,
                "net_result": 0,
            },
        )
        row["positions"] += 1
        row["wins"] += position["net_result"] > 0
        row["losses"] += position["net_result"] < 0
        category = exit_category(position)
        row[{"take": "takes", "stop": "stops"}.get(category, category)] += 1
        row["gross_result"] += position["gross_result"]
        row["commission"] += position["commission"]
        row["net_result"] += position["net_result"]

    for row in periods.values():
        row.update(win_rates(row["positions"], row["wins"], row["takes"], row["stops"]))

    return sorted(periods.values(), key=lambda row: row["period"], reverse=True)


def _filter_report_positions(positions, filters, period_length):
    result = []
    for position in positions:
        if position["status"] != "closed":
            continue

        family = ticker_family(position["ticker"])
        ticker = filters.get("ticker")
        mode = filters.get("ticker_mode")
        if ticker and mode == "only" and family != ticker:
            continue
        if ticker and mode == "exclude" and family == ticker:
            continue

        period = position["exit_at"][:period_length]
        if filters.get("period_from") and period < filters["period_from"]:
            continue
        if filters.get("period_to") and period > filters["period_to"]:
            continue
        result.append(position)
    return result


def monthly_report(positions, filters):
    """Retain the original monthly API response and filter names."""
    criteria = dict(filters) | {
        "group_by": "month",
        "period_from": filters.get("month_from"),
        "period_to": filters.get("month_to"),
    }
    return [{"month": row.pop("period"), **row} for row in trading_report(positions, criteria)]
