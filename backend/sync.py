from . import database
from .tbank import TBankClient, operation_trades


def sync_trades(token):
    client = TBankClient(token)
    instruments = database.get_instruments()
    saved = 0

    for account in client.accounts():
        database.save_account(account)
        account_trades = []

        for operation in client.operations(account["id"]):
            uid = operation.get("instrumentUid", "")
            if uid not in instruments:
                instruments[uid] = client.instrument(uid) if uid else {}
            account_trades.extend(operation_trades(account["id"], operation, instruments[uid]))

        saved += database.save_trades(account_trades)

    return saved

