"""Plan scenarios: authoring, position links, timeline notes and screenshots."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from ..config import DATA_DIR
from ..domain.journal import assess_exit
from ..domain.numbers import number_or_none
from ..domain.plans import (
    DIRECTION_LABELS,
    DIRECTIONS,
    effective_levels,
    entry_trade_id,
    plan_title,
    sort_plans_for_list,
    summarize_positions,
)
from ..storage import plans as storage
from .journal import get_journal_positions

ATTACHMENTS_DIR = DATA_DIR / "attachments"
MAX_ATTACHMENT_BYTES = 15 * 1024 * 1024
IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp"}


def now():
    return datetime.now(timezone.utc).isoformat()


def _json_load(value, fallback):
    try:
        return json.loads(value) if value else fallback
    except (TypeError, ValueError):
        return fallback


def _json_dump(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _body(body):
    if not isinstance(body, dict):
        raise ValueError("Ожидается JSON-объект")
    return body


def _text(body, key, default="", limit=50000):
    value = body.get(key, default)
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"Поле «{key}» должно быть строкой")
    if len(value) > limit:
        raise ValueError(f"Поле «{key}» длиннее {limit} символов")
    return value


def _direction(value):
    if value not in DIRECTIONS:
        raise ValueError("Направление должно быть long или short")
    return value


def _number_field(values, key, default=None, *, strict=True):
    value = values[key] if key in values else default
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    parsed = number_or_none(value)
    if parsed is None:
        if strict:
            raise ValueError(f"Поле «{key}» должно быть числом")
        return None
    return parsed


def _display_title(plan):
    ticker = (
        (plan.get("forecast") or {}).get("ticker")
        or (plan.get("execution") or {}).get("ticker")
        or "Без тикера"
    )
    direction = DIRECTION_LABELS.get(plan.get("direction"), "")
    return " · ".join(part for part in (ticker, direction) if part)


def _plan_response(row):
    plan = dict(row)
    plan.pop("status", None)
    plan.pop("origin", None)
    plan["forecast"] = _json_load(plan.pop("forecast_payload", "{}"), {})
    plan["execution"] = _json_load(plan.pop("execution_payload", "{}"), {})
    plan["title"] = _display_title(plan)
    return plan


def _attachment_response(row):
    attachment = dict(row)
    attachment["url"] = f"/api/attachments/{attachment['id']}"
    return attachment


def _positions():
    return {position["id"]: position for position in get_journal_positions({})}


def _link_values(plan_id, plan_row, position, source="manual"):
    closed = position["status"] == "closed"
    return {
        "plan_id": plan_id,
        "position_id": position["id"],
        "account_id": position["account_id"],
        "instrument_uid": position["instrument_uid"],
        "entry_trade_id": entry_trade_id(position),
        "direction": position["direction"],
        "link_source": source,
        "linked_at": now(),
        "planned_stop_override": "",
        "planned_take_override": "",
        "stop_at_close": (plan_row.get("planned_stop") or "") if closed else "",
        "take_at_close": (plan_row.get("planned_take") or "") if closed else "",
        "closed_at": position["exit_at"] if closed else None,
    }


def _decorate_position(position, plan_row, link):
    item = dict(position)
    stop, take = effective_levels(plan_row, link)
    item["planned_entry"] = plan_row.get("entry_zone")
    item["planned_stop"] = stop
    item["planned_take"] = take
    item["exit_assessment"] = assess_exit(item)
    item["plan_link"] = {
        "source": link.get("link_source"),
        "linked_at": link.get("linked_at"),
    }
    return item


def _detail(row):
    plan = _plan_response(row)
    positions = _positions()
    linked = []
    for link in storage.get_links_for_plan(row["id"]):
        position = positions.get(link["position_id"])
        if position:
            linked.append(_decorate_position(position, row, link))
    linked.sort(key=lambda position: position.get("entry_at") or "", reverse=True)
    plan["positions"] = linked
    plan["position_ids"] = [position["id"] for position in linked]
    plan["attachments"] = [
        _attachment_response(attachment) for attachment in storage.get_attachments(row["id"])
    ]
    plan["summary"] = summarize_positions(linked)
    return plan


def list_plans(filters):
    rows = storage.list_plans(filters)
    links_by_position = storage.get_links_by_position()
    links_by_plan = {}
    for link in links_by_position.values():
        links_by_plan.setdefault(link["plan_id"], []).append(link)
    positions = _positions()

    result = []
    for row in rows:
        plan = _plan_response(row)
        linked = [
            positions[link["position_id"]]
            for link in links_by_plan.get(row["id"], [])
            if link["position_id"] in positions
        ]
        plan["summary"] = summarize_positions(linked)
        plan["position_ids"] = [position["id"] for position in linked]
        result.append(plan)
    return sort_plans_for_list(result)


def available_positions(filters):
    linked = set(storage.get_links_by_position())
    return [
        position
        for position in get_journal_positions(filters or {})
        if position["id"] not in linked
    ]


def get_plan(plan_id):
    row = storage.get_plan(plan_id)
    if row is None:
        raise LookupError("План не найден")
    return _detail(row)


def _execution_from(values, position):
    if position is not None:
        provider = "tradingview" if position["account_id"].startswith("tradingview:") else "tbank"
        payload = {
            "provider": provider,
            "id": position["instrument_uid"],
            "ticker": position["ticker"],
            "name": position["instrument_name"],
            "currency": position["currency"],
            "price_precision": position["price_precision"],
            "platform": position.get("platform", ""),
        }
        return provider, position["instrument_uid"], _json_dump(payload)

    ticker = _text(values, "execution_ticker", "", 200).strip()
    name = _text(values, "execution_name", "", 200).strip() or ticker
    if not ticker:
        return None, None, "{}"
    return (
        "manual",
        ticker,
        _json_dump({"provider": "manual", "ticker": ticker, "name": name}),
    )


def _forecast_from(values):
    ticker = _text(values, "forecast_ticker", "", 200).strip()
    if not ticker:
        return None, None, "{}"
    return (
        "manual",
        ticker,
        _json_dump({"provider": "manual", "ticker": ticker, "name": ticker}),
    )


def _auto_title(values, position, execution):
    if position is not None:
        return plan_title(position)
    ticker = execution.get("ticker") if execution else ""
    direction = DIRECTION_LABELS.get(values["direction"], "")
    return " · ".join(part for part in (ticker or "Без тикера", direction) if part)


def create_plan(body):
    values = _body(body)
    position_id = values.get("position_id")
    if position_id is not None and not isinstance(position_id, str):
        raise ValueError("Идентификатор позиции должен быть строкой")
    position = None
    if position_id:
        position = _positions().get(position_id)
        if position is None:
            raise LookupError("Позиция не найдена")
        if storage.get_link_for_position(position_id):
            raise ValueError("Позиция уже привязана к плану")
        if values.get("direction") and values["direction"] != position["direction"]:
            raise ValueError("Направление позиции не совпадает с направлением плана")
        if values.get("account_id") and values["account_id"] != position["account_id"]:
            raise ValueError("Счёт позиции не совпадает со счётом плана")

    if values.get("account_id") is not None and not isinstance(values["account_id"], str):
        raise ValueError("Счёт должен быть строкой")

    direction = _direction(values.get("direction") or (position or {}).get("direction") or "long")

    execution_provider, execution_id, execution_payload = _execution_from(values, position)
    forecast_provider, forecast_id, forecast_payload = _forecast_from(values)
    execution = _json_load(execution_payload, {})
    forecast = _json_load(forecast_payload, {})
    title = _text(values, "title", "", 300).strip() or _auto_title(
        {"direction": direction}, position, execution or forecast
    )

    plan_id = str(uuid4())
    timestamp = now()
    default_thesis = position.get("entry_note", "") if position else ""
    default_review = position.get("exit_note", "") if position else ""
    plan = {
        "id": plan_id,
        "title": title,
        "thesis": _text(values, "thesis", default_thesis, 50000),
        "review": _text(values, "review", default_review, 50000),
        "direction": direction,
        "account_id": values.get("account_id") or (position or {}).get("account_id") or None,
        "forecast_provider": forecast_provider,
        "forecast_id": forecast_id,
        "forecast_payload": forecast_payload,
        "execution_provider": execution_provider,
        "execution_id": execution_id,
        "execution_payload": execution_payload,
        "entry_zone": _number_field(values, "entry_zone"),
        "planned_stop": _number_field(
            values,
            "planned_stop",
            position.get("planned_stop") if position else None,
            strict="planned_stop" in values,
        ),
        "planned_take": _number_field(
            values,
            "planned_take",
            position.get("planned_take") if position else None,
            strict="planned_take" in values,
        ),
        "planned_for": _text(values, "planned_for", "", 100) or None,
        "valid_until": _text(values, "valid_until", "", 100) or None,
        "parent_plan_id": None,
        "cover_attachment_id": None,
        "created_at": timestamp,
        "updated_at": timestamp,
    }

    link = _link_values(plan_id, plan, position, "manual") if position else None
    storage.create_plan_bundle(plan, link)
    return _detail(storage.get_plan(plan_id))


def update_plan(plan_id, body):
    values = _body(body)
    row = storage.get_plan(plan_id)
    if row is None:
        raise LookupError("План не найден")

    updates = {}

    def set_field(name, value):
        if row.get(name) != value:
            updates[name] = value

    for name, limit in (
        ("thesis", 50000),
        ("review", 50000),
        ("planned_for", 100),
        ("valid_until", 100),
    ):
        if name not in values:
            continue
        value = _text(values, name, "", limit)
        if name in {"planned_for", "valid_until"}:
            value = value or None
        set_field(name, value)
    linked_positions = None
    if "direction" in values or "account_id" in values:
        positions = _positions()
        linked_positions = [
            positions[link["position_id"]]
            for link in storage.get_links_for_plan(plan_id)
            if link["position_id"] in positions
        ]
    for name in ("entry_zone", "planned_stop", "planned_take"):
        if name in values:
            set_field(name, _number_field(values, name))
    if "direction" in values:
        direction = _direction(values["direction"])
        if linked_positions and any(
            position["direction"] != direction for position in linked_positions
        ):
            raise ValueError("Направление не совпадает с привязанными позициями")
        set_field("direction", direction)
    if "account_id" in values:
        account_id = values["account_id"] or None
        if account_id is not None and not isinstance(account_id, str):
            raise ValueError("Счёт должен быть строкой")
        if (
            account_id is not None
            and linked_positions
            and any(position["account_id"] != account_id for position in linked_positions)
        ):
            raise ValueError("Счёт не совпадает с привязанными позициями")
        set_field("account_id", account_id)
    if "forecast_ticker" in values:
        provider, forecast_id, payload = _forecast_from(values)
        set_field("forecast_provider", provider)
        set_field("forecast_id", forecast_id)
        set_field("forecast_payload", payload)
    if "execution_ticker" in values:
        provider, execution_id, payload = _execution_from(values, None)
        set_field("execution_provider", provider)
        set_field("execution_id", execution_id)
        set_field("execution_payload", payload)

    if not updates:
        return _detail(row)

    updates["updated_at"] = now()
    storage.update_plan_bundle(plan_id, updates)
    return _detail(storage.get_plan(plan_id))


def link_position(plan_id, position_id):
    row = storage.get_plan(plan_id)
    if row is None:
        raise LookupError("План не найден")
    position = _positions().get(position_id)
    if position is None:
        raise LookupError("Позиция не найдена")
    if storage.get_link_for_position(position_id):
        raise ValueError("Позиция уже привязана к плану")
    if row.get("direction") and row["direction"] != position["direction"]:
        raise ValueError("Направление позиции не совпадает с направлением плана")
    if row.get("account_id") and row["account_id"] != position["account_id"]:
        raise ValueError("Счёт позиции не совпадает со счётом плана")

    link = _link_values(plan_id, row, position, "manual")
    storage.create_link_bundle(link)
    return _detail(storage.get_plan(plan_id))


def unlink_position(plan_id, position_id):
    row = storage.get_plan(plan_id)
    if row is None:
        raise LookupError("План не найден")
    if not storage.delete_link_bundle(plan_id, position_id):
        raise LookupError("Позиция не привязана к этому плану")
    return _detail(storage.get_plan(plan_id))


def delete_plan(plan_id):
    row = storage.get_plan(plan_id)
    if row is None:
        raise LookupError("План не найден")
    if storage.get_links_for_plan(plan_id):
        raise ValueError("Нельзя удалить план с привязанными позициями. Сначала отвяжите их.")

    attachments = storage.get_attachments(plan_id)
    if not storage.delete_plan(plan_id):
        raise LookupError("План не найден")
    for attachment in attachments:
        try:
            _safe_attachment_path(attachment).unlink(missing_ok=True)
        except LookupError:
            pass
    return {"deleted": plan_id}


def _image_extension(data):
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    raise ValueError("Поддерживаются изображения PNG, JPEG и WebP")


def add_attachment(plan_id, upload, *, caption=""):
    row = storage.get_plan(plan_id)
    if row is None:
        raise LookupError("План не найден")
    if not isinstance(caption, str) or len(caption) > 500:
        raise ValueError("Подпись должна быть строкой до 500 символов")

    data = upload.read(MAX_ATTACHMENT_BYTES + 1)
    if not data:
        raise ValueError("Файл пустой")
    if len(data) > MAX_ATTACHMENT_BYTES:
        raise ValueError("Файл больше 15 МБ")
    extension = _image_extension(data)
    mime = IMAGE_TYPES[extension]

    directory = Path(ATTACHMENTS_DIR) / row["id"]
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{extension}"
    path = directory / filename
    path.write_bytes(data)

    existing = storage.get_attachments(plan_id)
    sort_order = max((item["sort_order"] for item in existing), default=0) + 1
    attachment = {
        "id": str(uuid4()),
        "plan_id": plan_id,
        "path": str(path.relative_to(Path(ATTACHMENTS_DIR))),
        "mime": mime,
        "size": len(data),
        "width": None,
        "height": None,
        "caption": caption.strip(),
        "sort_order": sort_order,
        "created_at": now(),
    }
    try:
        storage.create_attachment(attachment)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return _attachment_response(attachment)


def _safe_attachment_path(attachment):
    root = Path(ATTACHMENTS_DIR).resolve()
    path = (root / attachment["path"]).resolve()
    if root not in path.parents or not path.is_file():
        raise LookupError("Файл вложения не найден")
    return path


def attachment_file(attachment_id):
    attachment = storage.get_attachment(attachment_id)
    if attachment is None:
        raise LookupError("Вложение не найдено")
    return _safe_attachment_path(attachment), attachment["mime"]


def delete_attachment(attachment_id):
    attachment = storage.get_attachment(attachment_id)
    if attachment is None:
        raise LookupError("Вложение не найдено")
    try:
        _safe_attachment_path(attachment).unlink(missing_ok=True)
    except LookupError:
        pass
    storage.delete_attachment(attachment_id)
    return {"deleted": attachment_id}
