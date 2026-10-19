from ..domain.analytics import sort_positions
from ..domain.journal import JOURNAL_FIELDS, assess_exit
from ..domain.plans import effective_levels
from ..storage import database
from ..storage import plans as plan_storage
from .trading import get_positions


def get_journal_positions(filters):
    positions = get_positions(filters)
    notes = database.get_position_notes([position["id"] for position in positions])
    links = plan_storage.get_links_by_position()
    plans = plan_storage.get_plans_by_ids({link["plan_id"] for link in links.values()})
    for position in positions:
        position.update(notes.get(position["id"], {key: "" for key in JOURNAL_FIELDS}))
        link = links.get(position["id"])
        plan = plans.get(link["plan_id"]) if link else None
        if plan:
            # The plan is the authoring layer; a per-position override wins.
            position["planned_stop"], position["planned_take"] = effective_levels(plan, link)
            position["plan"] = {"id": plan["id"], "title": plan["title"]}
        position["exit_assessment"] = assess_exit(position)
    return sort_positions(positions, filters)


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
    effective = {**position, **values}
    link = plan_storage.get_link_for_position(position_id)
    plan = plan_storage.get_plan(link["plan_id"]) if link else None
    if plan:
        effective["planned_stop"], effective["planned_take"] = effective_levels(plan, link)
    return dict(**values, exit_assessment=assess_exit(effective))
