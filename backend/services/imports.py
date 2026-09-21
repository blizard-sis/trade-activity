import hashlib

from ..brokers.tradingview import parse_files
from ..storage import database


def import_tradingview_positions(files, account_name):
    name = account_name.strip()
    if not name or len(name) > 100:
        raise ValueError("Название счёта должно содержать от 1 до 100 символов")
    account_id = "tradingview:" + hashlib.sha256(name.encode()).hexdigest()[:24]
    positions, ignored = parse_files(files, account_id, f"TradingView · {name}")
    counts = database.save_imported_positions(positions)
    return dict(
        **counts, account_id=account_id, ignored=ignored,
        closed=sum(position["status"] == "closed" for position in positions),
        open=sum(position["status"] == "open" for position in positions),
    )
