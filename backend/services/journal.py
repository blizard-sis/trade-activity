from ..domain.journal import JOURNAL_FIELDS, assess_exit
from ..storage import database
from .trading import get_positions


def get_journal_positions(filters):
    positions = get_positions(filters)
    notes = database.get_position_notes([position["id"] for position in positions])
    for position in positions:
        position.update(notes.get(position["id"], {key: "" for key in JOURNAL_FIELDS}))
        position["exit_assessment"] = assess_exit(position)
    return positions


def update_journal(position_id, body):
    if not isinstance(body, dict):
        raise ValueError("Ожидается JSON-объект")
    values = {key: body.get(key, "") for key in JOURNAL_FIELDS}
    if any(not isinstance(value, str) or len(value) > 20000 for value in values.values()):
        raise ValueError("Поля дневника должны быть строками до 20 000 символов")
    position = next((item for item in get_positions({}) if item["id"] == position_id), None)
    if position is None:
        raise LookupError("Позиция не найдена")
    database.save_journal(position_id, values)
    return dict(**values, exit_assessment=assess_exit({**position, **values}))
