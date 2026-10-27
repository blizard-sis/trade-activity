"""SQLite access for plans, position links and attachments."""

from .database import transaction

PLAN_FIELDS = (
    "id",
    "title",
    "thesis",
    "review",
    "direction",
    "account_id",
    "forecast_provider",
    "forecast_id",
    "forecast_payload",
    "execution_provider",
    "execution_id",
    "execution_payload",
    "entry_zone",
    "planned_stop",
    "planned_take",
    "planned_for",
    "valid_until",
    "parent_plan_id",
    "cover_attachment_id",
    "created_at",
    "updated_at",
)

PLAN_EDITABLE_FIELDS = tuple(field for field in PLAN_FIELDS if field not in {"id", "created_at"})

LINK_FIELDS = (
    "plan_id",
    "position_id",
    "account_id",
    "instrument_uid",
    "entry_trade_id",
    "direction",
    "link_source",
    "linked_at",
    "planned_stop_override",
    "planned_take_override",
    "stop_at_close",
    "take_at_close",
    "closed_at",
)

ATTACHMENT_FIELDS = (
    "id",
    "plan_id",
    "path",
    "mime",
    "size",
    "width",
    "height",
    "caption",
    "sort_order",
    "created_at",
)


def _table_exists(db, name):
    return (
        db.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
        ).fetchone()
        is not None
    )


def _insert(db, table, fields, values):
    columns = ", ".join(fields)
    placeholders = ", ".join("?" for _ in fields)
    db.execute(
        f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
        [values[field] for field in fields],
    )


def create_plan_bundle(plan, link=None):
    with transaction() as db:
        _insert(db, "plans", PLAN_FIELDS, plan)
        if link is not None:
            _insert(db, "plan_positions", LINK_FIELDS, link)


def update_plan_bundle(plan_id, values):
    values = {key: value for key, value in values.items() if key in PLAN_EDITABLE_FIELDS}
    if not values:
        return False
    assignments = ", ".join(f"{field} = ?" for field in values)
    with transaction() as db:
        cursor = db.execute(
            f"UPDATE plans SET {assignments} WHERE id = ?",
            (*values.values(), plan_id),
        )
        if not cursor.rowcount:
            return False
        return True


def create_link_bundle(link):
    with transaction() as db:
        _insert(db, "plan_positions", LINK_FIELDS, link)


def delete_link_bundle(plan_id, position_id):
    with transaction() as db:
        cursor = db.execute(
            "DELETE FROM plan_positions WHERE plan_id = ? AND position_id = ?",
            (plan_id, position_id),
        )
        return bool(cursor.rowcount)


def get_plan(plan_id):
    with transaction() as db:
        if not _table_exists(db, "plans"):
            return None
        row = db.execute("SELECT * FROM plans WHERE id = ?", (plan_id,)).fetchone()
        return dict(row) if row else None


def list_plans(filters):
    conditions = []
    params = []
    account = filters.get("account")
    if account:
        conditions.append("account_id = ?")
        params.append(account)
    search = filters.get("search")
    if search:
        conditions.append(
            "(title LIKE ? OR thesis LIKE ? OR execution_payload LIKE ? OR forecast_payload LIKE ?)"
        )
        term = f"%{search}%"
        params.extend((term, term, term, term))

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    with transaction() as db:
        if not _table_exists(db, "plans"):
            return []
        rows = db.execute(
            f"SELECT * FROM plans {where} ORDER BY created_at DESC", params
        ).fetchall()
        return [dict(row) for row in rows]


def get_plans_by_ids(plan_ids):
    plan_ids = list(plan_ids)
    if not plan_ids:
        return {}
    placeholders = ", ".join("?" for _ in plan_ids)
    with transaction() as db:
        if not _table_exists(db, "plans"):
            return {}
        rows = db.execute(f"SELECT * FROM plans WHERE id IN ({placeholders})", plan_ids).fetchall()
        return {row["id"]: dict(row) for row in rows}


def get_links_by_position():
    with transaction() as db:
        if not _table_exists(db, "plan_positions"):
            return {}
        rows = db.execute("SELECT * FROM plan_positions").fetchall()
        return {row["position_id"]: dict(row) for row in rows}


def get_links_for_plan(plan_id):
    with transaction() as db:
        if not _table_exists(db, "plan_positions"):
            return []
        rows = db.execute(
            "SELECT * FROM plan_positions WHERE plan_id = ? ORDER BY linked_at", (plan_id,)
        ).fetchall()
        return [dict(row) for row in rows]


def get_link_for_position(position_id):
    with transaction() as db:
        if not _table_exists(db, "plan_positions"):
            return None
        row = db.execute(
            "SELECT * FROM plan_positions WHERE position_id = ?", (position_id,)
        ).fetchone()
        return dict(row) if row else None


def get_attachments(plan_id):
    with transaction() as db:
        if not _table_exists(db, "plan_attachments"):
            return []
        rows = db.execute(
            "SELECT * FROM plan_attachments WHERE plan_id = ? ORDER BY sort_order, created_at",
            (plan_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def get_attachment(attachment_id):
    with transaction() as db:
        if not _table_exists(db, "plan_attachments"):
            return None
        row = db.execute("SELECT * FROM plan_attachments WHERE id = ?", (attachment_id,)).fetchone()
        return dict(row) if row else None


def create_attachment(values):
    with transaction() as db:
        _insert(db, "plan_attachments", ATTACHMENT_FIELDS, values)


def delete_attachment(attachment_id):
    with transaction() as db:
        row = db.execute("SELECT * FROM plan_attachments WHERE id = ?", (attachment_id,)).fetchone()
        if not row:
            return None
        db.execute("DELETE FROM plan_attachments WHERE id = ?", (attachment_id,))
        return dict(row)


def delete_plan(plan_id):
    with transaction() as db:
        if not db.execute("SELECT 1 FROM plans WHERE id = ?", (plan_id,)).fetchone():
            return False
        db.execute("DELETE FROM plan_attachments WHERE plan_id = ?", (plan_id,))
        db.execute("DELETE FROM plans WHERE id = ?", (plan_id,))
        return True
