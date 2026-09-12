from ..domain.analytics import build_positions, filter_positions, monthly_report
from ..storage import database
from ..domain.accounts import selected_accounts


def get_positions(filters):
    positions = build_positions(database.get_trades(filters)) + database.get_imported_positions(filters)
    sources = {account["id"]: account for account in database.get_accounts()}
    for position in positions:
        source = sources.get(position["account_id"])
        if source:
            position["account_name"] = source["name"]
            position["platform"] = source["platform"]
    return filter_positions(positions, filters)


def get_monthly_report(filters):
    # Import here because the journal service also uses get_positions.
    from .journal import get_journal_positions
    return monthly_report(get_journal_positions({"account": selected_accounts(filters)}), filters)
