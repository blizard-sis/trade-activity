from decimal import Decimal

import truststore

truststore.inject_into_ssl()

import requests


API_URL = "https://invest-public-api.tbank.ru/rest/tinkoff.public.invest.api.contract.v1"
TRADE_TYPES = [
    "OPERATION_TYPE_BUY",
    "OPERATION_TYPE_BUY_CARD",
    "OPERATION_TYPE_BUY_MARGIN",
    "OPERATION_TYPE_SELL",
    "OPERATION_TYPE_SELL_CARD",
    "OPERATION_TYPE_SELL_MARGIN",
]


def money(value):
    if not value:
        return 0.0
    amount = Decimal(value.get("units", "0")) + Decimal(value.get("nano", 0)) / 1_000_000_000
    return float(amount)


class TBankClient:
    def __init__(self, token):
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def _post(self, service, method, payload):
        url = f"{API_URL}.{service}/{method}"
        response = self.session.post(url, json=payload, timeout=30)
        if not response.ok:
            message = response.json().get("message", response.text)
            raise RuntimeError(f"T-Bank API: {message}")
        return response.json()

    def accounts(self):
        data = self._post("UsersService", "GetAccounts", {"status": "ACCOUNT_STATUS_ALL"})
        return data.get("accounts", [])

    def operations(self, account_id):
        cursor = ""
        while True:
            payload = {
                "accountId": account_id,
                "cursor": cursor,
                "limit": 1000,
                "operationTypes": TRADE_TYPES,
                "state": "OPERATION_STATE_EXECUTED",
                "withoutTrades": False,
            }
            page = self._post("OperationsService", "GetOperationsByCursor", payload)
            yield from page.get("items", [])
            if not page.get("hasNext"):
                break
            cursor = page["nextCursor"]

    def instrument(self, uid):
        data = self._post("InstrumentsService", "FindInstrument", {"query": uid})
        instruments = data.get("instruments", [])
        exact = next((item for item in instruments if item.get("uid") == uid), None)
        return exact or (instruments[0] if instruments else {})


def operation_trades(account_id, operation, instrument):
    trades = operation.get("trades") or operation.get("tradesInfo", {}).get("trades", [])
    total_quantity = sum(int(trade.get("quantity", 0)) for trade in trades)
    commission = money(operation.get("commission"))
    payment = money(operation.get("payment"))
    side = "sell" if "SELL" in operation.get("type", "") else "buy"

    for index, trade in enumerate(trades):
        quantity = int(trade.get("quantity", 0))
        yield {
            "account_id": account_id,
            "trade_id": trade.get("tradeId") or trade.get("num") or f'{operation["id"]}:{index}',
            "operation_id": operation.get("id", ""),
            "instrument_uid": operation.get("instrumentUid", ""),
            "ticker": instrument.get("ticker", ""),
            "instrument_name": instrument.get("name", ""),
            "side": side,
            "quantity": quantity,
            "price": money(trade.get("price")),
            "currency": trade.get("price", {}).get("currency", ""),
            "commission": commission * quantity / total_quantity if total_quantity else 0,
            "commission_currency": operation.get("commission", {}).get("currency", ""),
            "payment": payment * quantity / total_quantity if total_quantity else 0,
            "payment_currency": operation.get("payment", {}).get("currency", ""),
            "executed_at": trade.get("dateTime") or trade.get("date") or operation.get("date", ""),
        }
