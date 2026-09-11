from datetime import datetime, timezone


def build_export_document(positions, filters):
    document = {
        "format": "trade-activity",
        "version": 1,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "filters": {
            key: value
            for key, value in filters.items()
            if key not in {"sort", "direction_sort"}
        },
        "summary": _export_summary(positions),
        "positions": [_export_position(position) for position in positions],
    }
    return document


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
        "planned_stop": position["planned_stop"],
        "planned_take": position["planned_take"],
        "exit_assessment": position["exit_assessment"],
    }
