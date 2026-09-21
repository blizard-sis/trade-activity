from ..domain.accounts import selected_accounts
from ..domain.analytics import monthly_report
from .journal import get_journal_positions


def get_monthly_report(filters):
    positions = get_journal_positions({"account": selected_accounts(filters)})
    return monthly_report(positions, filters)
