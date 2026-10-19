import json
import sqlite3
from contextlib import contextmanager

from ..config import ROOT
from ..domain.accounts import account_source, selected_accounts
from ..domain.journal import JOURNAL_FIELDS
from ..domain.numbers import number_or_none

DATABASE = ROOT / "trade_activity.sqlite3"
TRADE_FIELDS = (
    "account_id",
    "trade_id",
    "operation_id",
    "instrument_uid",
    "ticker",
    "instrument_name",
    "side",
    "quantity",
    "price",
    "currency",
    "commission",
    "commission_currency",
    "payment",
    "payment_currency",
    "executed_at",
)


def connect():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def transaction():
    """Commit or roll back, and always close the SQLite connection."""
    connection = connect()
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize():
    with transaction() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                status TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS trades (
                account_id TEXT NOT NULL,
                trade_id TEXT NOT NULL,
                operation_id TEXT NOT NULL,
                instrument_uid TEXT NOT NULL,
                ticker TEXT NOT NULL,
                instrument_name TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                currency TEXT NOT NULL,
                commission REAL NOT NULL,
                commission_currency TEXT NOT NULL DEFAULT '',
                payment REAL NOT NULL DEFAULT 0,
                payment_currency TEXT NOT NULL DEFAULT '',
                executed_at TEXT NOT NULL,
                PRIMARY KEY (account_id, trade_id),
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS instrument_catalog (
                provider TEXT NOT NULL,
                instrument_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                PRIMARY KEY (provider, instrument_id)
            );

            CREATE TABLE IF NOT EXISTS instrument_links (
                id TEXT PRIMARY KEY,
                forecast_provider TEXT NOT NULL,
                forecast_id TEXT NOT NULL,
                execution_provider TEXT NOT NULL,
                execution_id TEXT NOT NULL,
                UNIQUE (forecast_provider, forecast_id, execution_provider, execution_id),
                FOREIGN KEY (forecast_provider, forecast_id) REFERENCES instrument_catalog(provider, instrument_id),
                FOREIGN KEY (execution_provider, execution_id) REFERENCES instrument_catalog(provider, instrument_id)
            );

            CREATE TABLE IF NOT EXISTS imported_positions (
                id TEXT PRIMARY KEY,
                account_id TEXT NOT NULL,
                payload TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS position_notes (
                position_id TEXT PRIMARY KEY,
                entry_note TEXT NOT NULL DEFAULT '',
                exit_note TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS plans (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL DEFAULT '',
                thesis TEXT NOT NULL DEFAULT '',
                review TEXT NOT NULL DEFAULT '',
                direction TEXT NOT NULL DEFAULT ''
                    CHECK (direction IN ('', 'long', 'short')),
                account_id TEXT,
                forecast_provider TEXT,
                forecast_id TEXT,
                forecast_payload TEXT NOT NULL DEFAULT '{}',
                execution_provider TEXT,
                execution_id TEXT,
                execution_payload TEXT NOT NULL DEFAULT '{}',
                entry_zone REAL,
                planned_stop REAL,
                planned_take REAL,
                planned_for TEXT,
                valid_until TEXT,
                parent_plan_id TEXT,
                cover_attachment_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (account_id) REFERENCES accounts(id),
                FOREIGN KEY (parent_plan_id) REFERENCES plans(id)
            );

            CREATE TABLE IF NOT EXISTS plan_positions (
                plan_id TEXT NOT NULL,
                position_id TEXT NOT NULL,
                account_id TEXT NOT NULL,
                instrument_uid TEXT NOT NULL,
                entry_trade_id TEXT NOT NULL DEFAULT '',
                direction TEXT NOT NULL CHECK (direction IN ('long', 'short')),
                link_source TEXT NOT NULL DEFAULT 'manual'
                    CHECK (link_source IN ('manual', 'auto', 'migration')),
                linked_at TEXT NOT NULL,
                planned_stop_override TEXT NOT NULL DEFAULT '',
                planned_take_override TEXT NOT NULL DEFAULT '',
                stop_at_close TEXT NOT NULL DEFAULT '',
                take_at_close TEXT NOT NULL DEFAULT '',
                closed_at TEXT,
                PRIMARY KEY (plan_id, position_id),
                UNIQUE (position_id),
                FOREIGN KEY (plan_id) REFERENCES plans(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS plan_attachments (
                id TEXT PRIMARY KEY,
                plan_id TEXT NOT NULL,
                path TEXT NOT NULL,
                mime TEXT NOT NULL,
                size INTEGER NOT NULL,
                width INTEGER,
                height INTEGER,
                caption TEXT NOT NULL DEFAULT '',
                sort_order INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (plan_id) REFERENCES plans(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS sync_runs (
                id TEXT PRIMARY KEY,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT NOT NULL,
                accounts INTEGER NOT NULL DEFAULT 0,
                added INTEGER NOT NULL DEFAULT 0,
                updated INTEGER NOT NULL DEFAULT 0,
                unchanged INTEGER NOT NULL DEFAULT 0,
                error TEXT NOT NULL DEFAULT '',
                changes TEXT NOT NULL DEFAULT '[]'
            );

            CREATE INDEX IF NOT EXISTS imported_positions_account ON imported_positions(account_id);
            CREATE INDEX IF NOT EXISTS trades_date ON trades(executed_at);
            CREATE INDEX IF NOT EXISTS trades_ticker ON trades(ticker);
            CREATE INDEX IF NOT EXISTS plans_created ON plans(created_at);
            CREATE INDEX IF NOT EXISTS plans_account ON plans(account_id);
            CREATE INDEX IF NOT EXISTS plans_execution
                ON plans(execution_provider, execution_id);
            CREATE INDEX IF NOT EXISTS plan_attachments_plan
                ON plan_attachments(plan_id, sort_order);
            CREATE INDEX IF NOT EXISTS sync_runs_started ON sync_runs(started_at);
            """
        )
        _migrate_trades(db)
        note_columns = {row["name"] for row in db.execute("PRAGMA table_info(position_notes)")}
        for name in ("planned_stop", "planned_take"):
            if name not in note_columns:
                db.execute(f"ALTER TABLE position_notes ADD COLUMN {name} TEXT NOT NULL DEFAULT ''")
        _migrate_plans(db)
        _migrate_plan_numbers(db)
        _migrate_plan_attachments(db)
        db.execute("DROP TABLE IF EXISTS plan_events")
        db.execute("PRAGMA optimize")


def _migrate_plan_numbers(db):
    """Convert plan price fields from free text to REAL values."""
    columns = {
        row["name"]: (row["type"] or "").upper() for row in db.execute("PRAGMA table_info(plans)")
    }
    if all(
        "REAL" in columns.get(name, "") for name in ("entry_zone", "planned_stop", "planned_take")
    ):
        return

    fields = (
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
    rows = db.execute("SELECT * FROM plans").fetchall()
    db.execute("DROP TABLE IF EXISTS plans_numbers")
    db.execute(
        """
        CREATE TABLE plans_numbers (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL DEFAULT '',
            thesis TEXT NOT NULL DEFAULT '',
            review TEXT NOT NULL DEFAULT '',
            direction TEXT NOT NULL DEFAULT ''
                CHECK (direction IN ('', 'long', 'short')),
            account_id TEXT,
            forecast_provider TEXT,
            forecast_id TEXT,
            forecast_payload TEXT NOT NULL DEFAULT '{}',
            execution_provider TEXT,
            execution_id TEXT,
            execution_payload TEXT NOT NULL DEFAULT '{}',
            entry_zone REAL,
            planned_stop REAL,
            planned_take REAL,
            planned_for TEXT,
            valid_until TEXT,
            parent_plan_id TEXT,
            cover_attachment_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (account_id) REFERENCES accounts(id),
            FOREIGN KEY (parent_plan_id) REFERENCES plans(id)
        )
        """
    )
    placeholders = ", ".join("?" for _ in fields)
    sql = f"INSERT INTO plans_numbers ({', '.join(fields)}) VALUES ({placeholders})"
    for row in rows:
        values = [
            number_or_none(row[name])
            if name in {"entry_zone", "planned_stop", "planned_take"}
            else row[name]
            for name in fields
        ]
        db.execute(sql, values)
    db.execute("DROP TABLE plans")
    db.execute("ALTER TABLE plans_numbers RENAME TO plans")
    db.executescript(
        """
        CREATE INDEX IF NOT EXISTS plans_created ON plans(created_at);
        CREATE INDEX IF NOT EXISTS plans_account ON plans(account_id);
        CREATE INDEX IF NOT EXISTS plans_execution
            ON plans(execution_provider, execution_id);
        """
    )


def _migrate_plan_attachments(db):
    """Drop timeline references and stages from plan attachments."""
    columns = {row["name"] for row in db.execute("PRAGMA table_info(plan_attachments)")}
    if "event_id" not in columns and "stage" not in columns:
        return
    db.execute("DROP TABLE IF EXISTS plan_attachments_new")
    db.execute(
        """
        CREATE TABLE plan_attachments_new (
            id TEXT PRIMARY KEY,
            plan_id TEXT NOT NULL,
            path TEXT NOT NULL,
            mime TEXT NOT NULL,
            size INTEGER NOT NULL,
            width INTEGER,
            height INTEGER,
            caption TEXT NOT NULL DEFAULT '',
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (plan_id) REFERENCES plans(id) ON DELETE CASCADE
        )
        """
    )
    db.execute(
        """
        INSERT INTO plan_attachments_new (
            id, plan_id, path, mime, size, width, height, caption, sort_order, created_at
        )
        SELECT id, plan_id, path, mime, size, width, height, caption, sort_order, created_at
        FROM plan_attachments
        """
    )
    db.execute("DROP TABLE plan_attachments")
    db.execute("ALTER TABLE plan_attachments_new RENAME TO plan_attachments")
    db.execute(
        "CREATE INDEX IF NOT EXISTS plan_attachments_plan ON plan_attachments(plan_id, sort_order)"
    )


def _migrate_plans(db):
    """Drop the obsolete migration marker and status workflow from plans."""
    columns = {row["name"] for row in db.execute("PRAGMA table_info(plans)")}
    if not {"origin", "status", "tags", "entry_method"} & columns:
        return
    db.executescript(
        """
        DROP TABLE IF EXISTS plans_new;
        CREATE TABLE plans_new (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL DEFAULT '',
            thesis TEXT NOT NULL DEFAULT '',
            review TEXT NOT NULL DEFAULT '',
            direction TEXT NOT NULL DEFAULT ''
                CHECK (direction IN ('', 'long', 'short')),
            account_id TEXT,
            forecast_provider TEXT,
            forecast_id TEXT,
            forecast_payload TEXT NOT NULL DEFAULT '{}',
            execution_provider TEXT,
            execution_id TEXT,
            execution_payload TEXT NOT NULL DEFAULT '{}',
            entry_zone TEXT NOT NULL DEFAULT '',
            planned_stop TEXT NOT NULL DEFAULT '',
            planned_take TEXT NOT NULL DEFAULT '',
            planned_for TEXT,
            valid_until TEXT,
            parent_plan_id TEXT,
            cover_attachment_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (account_id) REFERENCES accounts(id),
            FOREIGN KEY (parent_plan_id) REFERENCES plans(id)
        );
        INSERT INTO plans_new (
            id, title, thesis, review, direction, account_id,
            forecast_provider, forecast_id, forecast_payload,
            execution_provider, execution_id, execution_payload,
            entry_zone, planned_stop, planned_take,
            planned_for, valid_until, parent_plan_id,
            cover_attachment_id, created_at, updated_at
        )
        SELECT
            id, title, thesis, review, direction, account_id,
            forecast_provider, forecast_id, forecast_payload,
            execution_provider, execution_id, execution_payload,
            entry_zone, planned_stop, planned_take,
            planned_for, valid_until, parent_plan_id,
            cover_attachment_id, created_at, updated_at
        FROM plans;
        DROP TABLE plans;
        ALTER TABLE plans_new RENAME TO plans;
        CREATE INDEX IF NOT EXISTS plans_created ON plans(created_at);
        CREATE INDEX IF NOT EXISTS plans_account ON plans(account_id);
        CREATE INDEX IF NOT EXISTS plans_execution
            ON plans(execution_provider, execution_id);
        """
    )


def _migrate_trades(db):
    columns = {row["name"] for row in db.execute("PRAGMA table_info(trades)")}
    migrations = {
        "commission_currency": "TEXT NOT NULL DEFAULT ''",
        "payment": "REAL NOT NULL DEFAULT 0",
        "payment_currency": "TEXT NOT NULL DEFAULT ''",
    }
    for name, definition in migrations.items():
        if name not in columns:
            db.execute(f"ALTER TABLE trades ADD COLUMN {name} {definition}")


def save_account(account):
    values = (
        account["id"],
        account.get("name") or account["id"],
        account.get("type", ""),
        account.get("status", ""),
    )
    with transaction() as db:
        db.execute(
            """
            INSERT INTO accounts VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                type = excluded.type,
                status = excluded.status
            """,
            values,
        )


def save_trades(trades, *, with_counts=False):
    rows = list(
        {
            (trade["account_id"], trade["trade_id"]): tuple(trade[field] for field in TRADE_FIELDS)
            for trade in trades
        }.values()
    )
    counts = dict(added=0, updated=0, unchanged=0)
    if not rows:
        return counts if with_counts else 0

    placeholders = ", ".join("?" for _ in TRADE_FIELDS)
    updates = ", ".join(f"{field} = excluded.{field}" for field in TRADE_FIELDS[2:])
    sql = (
        f"INSERT INTO trades ({', '.join(TRADE_FIELDS)}) VALUES ({placeholders}) "
        f"ON CONFLICT(account_id, trade_id) DO UPDATE SET {updates}"
    )
    with transaction() as db:
        for row in rows:
            previous = db.execute(
                f"SELECT {', '.join(TRADE_FIELDS)} FROM trades WHERE account_id = ? AND trade_id = ?",
                row[:2],
            ).fetchone()
            category = (
                "added"
                if previous is None
                else "unchanged"
                if tuple(previous) == row
                else "updated"
            )
            counts[category] += 1
            if category != "unchanged":
                db.execute(sql, row)
    return counts if with_counts else len(rows)


def get_accounts():
    with transaction() as db:
        return [
            account_source(dict(row)) for row in db.execute("SELECT * FROM accounts ORDER BY name")
        ]


def get_instruments():
    sql = "SELECT instrument_uid, ticker, instrument_name FROM trades GROUP BY instrument_uid"
    with transaction() as db:
        return {
            row["instrument_uid"]: {"ticker": row["ticker"], "name": row["instrument_name"]}
            for row in db.execute(sql)
        }


def get_tickers(account_id=None):
    sql = "SELECT DISTINCT ticker FROM trades WHERE ticker != ''"
    params = []
    ids = selected_accounts({"account": account_id})
    if ids:
        sql += f" AND account_id IN ({','.join('?' for _ in ids)})"
        params.extend(ids)
    sql += " ORDER BY ticker"

    with transaction() as db:
        values = {row["ticker"] for row in db.execute(sql, params)}
    values.update(p["ticker"] for p in get_imported_positions({"account": account_id}))
    return sorted(values)


def get_imported_positions(filters):
    ids = selected_accounts(filters)
    sql = "SELECT payload FROM imported_positions"
    if ids:
        sql += f" WHERE account_id IN ({','.join('?' for _ in ids)})"
    with transaction() as db:
        rows = db.execute(sql, ids).fetchall()
    positions = [json.loads(row["payload"]) for row in rows]
    if filters.get("search"):
        term = filters["search"].casefold()
        positions = [
            p
            for p in positions
            if term in p["ticker"].casefold() or term in p["instrument_name"].casefold()
        ]
    return positions


def save_imported_positions(positions):
    counts = dict(added=0, updated=0, unchanged=0)
    if not positions:
        return counts
    with transaction() as db:
        first = positions[0]
        db.execute(
            "INSERT OR IGNORE INTO accounts VALUES (?, ?, 'paper', 'active')",
            (first["account_id"], first["account_name"]),
        )
        for position in positions:
            old = db.execute(
                "SELECT payload FROM imported_positions WHERE id = ?", (position["id"],)
            ).fetchone()
            if old:
                previous = json.loads(old["payload"])
                # A previously closed position must not reopen after an older export.
                if previous["status"] == "closed" and position["status"] == "open":
                    counts["unchanged"] += 1
                    continue
                _preserve_import_details(position, previous)
            payload = json.dumps(position, ensure_ascii=False, sort_keys=True)
            if old and old["payload"] == payload:
                counts["unchanged"] += 1
                continue
            counts["updated" if old else "added"] += 1
            db.execute(
                "INSERT INTO imported_positions VALUES (?, ?, ?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload",
                (position["id"], position["account_id"], payload),
            )
    return counts


def _preserve_import_details(position, previous):
    """Keep precise values when a later import omits supporting TradingView tabs."""
    for field in ("entry_at", "exit_at"):
        if (
            previous[field]
            and position[field]
            and previous[field][:16] == position[field][:16]
            and position[field].endswith(":00")
        ):
            position[field] = previous[field]
    if not position["currency"]:
        position["currency"] = previous["currency"]
    if (
        previous["net_result"] is not None
        and position["net_result"] is not None
        and abs(previous["net_result"] - position["net_result"]) < 0.011
        and position["net_result"] == round(position["net_result"], 2)
    ):
        position["net_result"] = previous["net_result"]
        position["gross_result"] = position["net_result"] + position["commission"]


def get_setting(key):
    with transaction() as db:
        row = db.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None


def save_setting(key, value):
    with transaction() as db:
        db.execute(
            "INSERT INTO settings VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


def delete_setting(key):
    with transaction() as db:
        db.execute("DELETE FROM settings WHERE key = ?", (key,))


def get_position_notes(position_ids):
    if not position_ids:
        return {}

    placeholders = ", ".join("?" for _ in position_ids)
    sql = f"""
        SELECT *
        FROM position_notes
        WHERE position_id IN ({placeholders})
    """
    with transaction() as db:
        return {
            row["position_id"]: {key: row[key] for key in JOURNAL_FIELDS}
            for row in db.execute(sql, position_ids)
        }


def save_position_notes(position_id, entry_note, exit_note):
    with transaction() as db:
        db.execute(
            """
            INSERT INTO position_notes (position_id, entry_note, exit_note)
            VALUES (?, ?, ?)
            ON CONFLICT(position_id) DO UPDATE SET
                entry_note = excluded.entry_note,
                exit_note = excluded.exit_note,
                updated_at = CURRENT_TIMESTAMP
            """,
            (position_id, entry_note, exit_note),
        )


def save_journal(position_id, values):
    columns = ", ".join(JOURNAL_FIELDS)
    placeholders = ", ".join("?" for _ in JOURNAL_FIELDS)
    updates = ", ".join(f"{key} = excluded.{key}" for key in JOURNAL_FIELDS)
    with transaction() as db:
        db.execute(
            f"INSERT INTO position_notes (position_id, {columns}) VALUES (?, {placeholders}) "
            f"ON CONFLICT(position_id) DO UPDATE SET {updates}, updated_at = CURRENT_TIMESTAMP",
            (position_id, *(values[key] for key in JOURNAL_FIELDS)),
        )


def get_trades(filters):
    conditions = []
    params = []

    ids = selected_accounts(filters)
    if ids:
        conditions.append(f"trades.account_id IN ({','.join('?' for _ in ids)})")
        params.extend(ids)
    if filters.get("search"):
        conditions.append("(ticker LIKE ? OR instrument_name LIKE ?)")
        search = f"%{filters['search']}%"
        params.extend((search, search))

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"""
        SELECT trades.*, accounts.name AS account_name
        FROM trades
        JOIN accounts ON accounts.id = trades.account_id
        {where}
    """
    with transaction() as db:
        return [dict(row) for row in db.execute(sql, params)]
