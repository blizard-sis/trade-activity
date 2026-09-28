from datetime import datetime, timezone
from uuid import uuid4

from ..brokers.tbank_mcp import TBankMCPClient
from ..storage import instruments as storage


def search_instruments(token, query):
    if not isinstance(query, str) or not 2 <= len(query.strip()) <= 100:
        raise ValueError("Введите от 2 до 100 символов для поиска")
    with TBankMCPClient(token) as client:
        items = client.search(query.strip())
    items.sort(
        key=lambda item: (
            not item.get("apiTradeAvailableFlag", False),
            item.get("ticker", ""),
            item.get("classCode", ""),
        )
    )
    return [
        dict(
            id=item["uid"],
            provider="tbank",
            ticker=item.get("ticker", ""),
            name=item["name"],
            class_code=item.get("classCode", ""),
            kind=item["instrumentKind"],
        )
        for item in items
        if item.get("uid")
    ]


def _snapshot(client, instrument_id, kind):
    data = client.instrument(instrument_id, kind)
    exchange_code = data["exchange"]
    exchange = "MOEX" if exchange_code.lower().startswith(("moex", "forts")) else exchange_code
    return dict(
        provider="tbank",
        id=data["uid"],
        ticker=data["ticker"],
        name=data.get("name", ""),
        exchange=exchange,
        exchange_code=exchange_code,
        class_code=data.get("classCode", ""),
        kind=kind,
        expiration_at=data.get("expirationDate", ""),
        currency=data.get("currency", ""),
        lot=data.get("lot"),
        tick_size=data.get("minPriceIncrement", {}).get("value"),
        tick_value=data.get("minPriceIncrementAmount", {}).get("value"),
        underlying_id=data.get("basicAssetPositionUid", ""),
        updated_at=datetime.now(timezone.utc).isoformat(),
    )


def select_instrument(token, instrument_id, kind):
    if not isinstance(instrument_id, str) or not 1 <= len(instrument_id) <= 100:
        raise ValueError("Некорректный идентификатор инструмента")
    with TBankMCPClient(token) as client:
        item = _snapshot(client, instrument_id, kind)
    storage.save_instruments([item])
    return item


def save_link(body, link_id=None):
    if not isinstance(body, dict):
        raise ValueError("Ожидается объект со связкой инструментов")
    selected = []
    for role in ("forecast", "execution"):
        value = body.get(role)
        if (
            not isinstance(value, dict)
            or value.get("provider") != "tbank"
            or not isinstance(value.get("id"), str)
        ):
            raise ValueError("Выберите оба инструмента из справочника")
        item = storage.get_instrument(value["provider"], value["id"])
        if not item:
            raise ValueError("Инструмент не найден в справочнике. Повторите поиск")
        selected.append(item)
    update = link_id is not None
    link_id = link_id or str(uuid4())
    storage.save_link(link_id, *selected, update=update)
    return dict(id=link_id, forecast=selected[0], execution=selected[1])


def refresh_link(token, link_id):
    link = storage.get_link(link_id)
    if not link:
        raise LookupError("Связка не найдена")
    with TBankMCPClient(token) as client:
        items = [
            _snapshot(client, link[role]["id"], link[role]["kind"])
            for role in ("forecast", "execution")
        ]
    storage.save_instruments(items)
    return dict(id=link_id, forecast=items[0], execution=items[1])
