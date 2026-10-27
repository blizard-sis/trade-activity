"""Pure helpers for plans: titles, stable position identity and summaries."""

from datetime import datetime

DIRECTIONS = ("long", "short")
DIRECTION_LABELS = {"long": "Лонг", "short": "Шорт"}


def display_date(value):
    if not value:
        return ""
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).strftime("%d.%m.%Y")
    except ValueError:
        return str(value)[:10]


def plan_title(position):
    ticker = position.get("ticker") or position.get("instrument_name") or "Без тикера"
    direction = DIRECTION_LABELS.get(position.get("direction"), "")
    return " · ".join(
        part for part in (ticker, direction, display_date(position.get("entry_at"))) if part
    )


def entry_trade_id(position):
    value = position.get("entry_trade_id")
    if value:
        return str(value)

    # Older TradingView payloads only have the composed position id. The order
    # id is the last segment, so a right split avoids splitting the symbol.
    identifier = position.get("id") or ""
    account_id = position.get("account_id") or ""
    direction = position.get("direction") or ""
    prefix = f"{account_id}:"
    suffix = f":{direction}"
    if identifier.startswith(prefix) and identifier.endswith(suffix):
        middle = identifier[len(prefix) : -len(suffix)]
        return middle.rsplit(":", 1)[-1] if ":" in middle else middle
    return ""


def effective_levels(plan, link=None):
    """Plan levels are authoritative; a per-position override wins over them."""
    link = link or {}
    stop = link.get("planned_stop_override")
    if stop in (None, ""):
        stop = plan.get("planned_stop")
    take = link.get("planned_take_override")
    if take in (None, ""):
        take = plan.get("planned_take")
    return ("" if stop is None else stop, "" if take is None else take)


def summarize_positions(positions):
    closed = [position for position in positions if position.get("status") == "closed"]
    net = {}
    for position in closed:
        currency = (position.get("result_currency") or "rub").upper()
        net[currency] = net.get(currency, 0) + (position.get("net_result") or 0)
    entries = [position["entry_at"] for position in positions if position.get("entry_at")]
    exits = [position["exit_at"] for position in positions if position.get("exit_at")]
    return {
        "positions": len(positions),
        "open": len(positions) - len(closed),
        "closed": len(closed),
        "net": {currency: round(value, 2) for currency, value in sorted(net.items())},
        "first_entry_at": min(entries) if entries else None,
        "last_exit_at": max(exits) if exits else None,
    }


def _plan_list_group(plan):
    summary = plan.get("summary") or {}
    if not summary.get("positions"):
        return 0
    if summary.get("open"):
        return 1
    return 2


def _plan_list_date(plan):
    summary = plan.get("summary") or {}
    if not summary.get("positions"):
        return plan.get("created_at") or ""
    if summary.get("open"):
        return summary.get("first_entry_at") or plan.get("created_at") or ""
    return summary.get("last_exit_at") or plan.get("created_at") or ""


def sort_plans_for_list(plans):
    """Ideas without positions first, then open positions, then closed history."""
    ordered = sorted(plans, key=_plan_list_date, reverse=True)
    ordered.sort(key=_plan_list_group)
    return ordered
