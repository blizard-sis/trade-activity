from ..domain.accounts import selected_accounts
from ..domain.reports import monthly_report, trading_report
from .journal import get_journal_positions


def get_monthly_report(filters):
    positions = get_journal_positions({"account": selected_accounts(filters)})
    return monthly_report(positions, filters)


def get_trading_report(filters):
    if filters.get("group_by", "month") not in {"month", "day"}:
        raise ValueError("Неизвестная группировка отчёта")
    positions = get_journal_positions({"account": selected_accounts(filters)})
    return trading_report(positions, filters)
