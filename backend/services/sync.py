from ..storage import database
from ..brokers.tbank import TBankClient, operation_trades


def sync_trades(token):
    client = TBankClient(token)
    instruments = database.get_instruments()
    result = dict(added=0, updated=0, unchanged=0, accounts=0)

    for account in client.accounts():
        database.save_account(account)
        account_trades = []

        for operation in client.operations(account["id"]):
            uid = operation.get("instrumentUid", "")
            if uid not in instruments:
                instruments[uid] = client.instrument(uid) if uid else {}
            account_trades.extend(operation_trades(account["id"], operation, instruments[uid]))

        counts = database.save_trades(account_trades, with_counts=True)
        result["accounts"] += 1
        for key, value in counts.items():
            result[key] += value

    result["saved"] = result["added"] + result["updated"] + result["unchanged"]
    return result

