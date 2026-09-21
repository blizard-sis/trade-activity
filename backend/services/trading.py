from ..domain.analytics import build_positions, filter_positions
from ..storage import database


def get_positions(filters):
    positions = build_positions(database.get_trades(filters)) + database.get_imported_positions(filters)
    sources = {account["id"]: account for account in database.get_accounts()}
    for position in positions:
        source = sources.get(position["account_id"])
        if source:
            position["account_name"] = source["name"]
            position["platform"] = source["platform"]
    return filter_positions(positions, filters)
