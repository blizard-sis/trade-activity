import sqlite3

from .config import ROOT


DATABASE = ROOT / "trade_activity.sqlite3"
TRADE_FIELDS = (
    "account_id", "trade_id", "operation_id", "instrument_uid", "ticker",
    "instrument_name", "side", "quantity", "price", "currency", "commission",
    "commission_currency", "payment", "payment_currency", "executed_at",
)


def connect():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize():
    with connect() as db:
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

            CREATE TABLE IF NOT EXISTS position_notes (
                position_id TEXT PRIMARY KEY,
                entry_note TEXT NOT NULL DEFAULT '',
                exit_note TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS trades_date ON trades(executed_at);
            CREATE INDEX IF NOT EXISTS trades_ticker ON trades(ticker);
            """
        )
        _migrate_trades(db)
        db.execute("PRAGMA optimize")


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
    with connect() as db:
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


def save_trades(trades):
    rows = [tuple(trade[field] for field in TRADE_FIELDS) for trade in trades]
    if not rows:
        return 0

    placeholders = ", ".join("?" for _ in TRADE_FIELDS)
    updates = ", ".join(f"{field} = excluded.{field}" for field in TRADE_FIELDS[2:])
    sql = (
        f"INSERT INTO trades ({', '.join(TRADE_FIELDS)}) VALUES ({placeholders}) "
        f"ON CONFLICT(account_id, trade_id) DO UPDATE SET {updates}"
    )
    with connect() as db:
        db.executemany(sql, rows)
    return len(rows)


def get_accounts():
    with connect() as db:
        return [dict(row) for row in db.execute("SELECT * FROM accounts ORDER BY name")]


def get_instruments():
    sql = "SELECT instrument_uid, ticker, instrument_name FROM trades GROUP BY instrument_uid"
    with connect() as db:
        return {
            row["instrument_uid"]: {"ticker": row["ticker"], "name": row["instrument_name"]}
            for row in db.execute(sql)
        }


def get_tickers(account_id=None):
    sql = "SELECT DISTINCT ticker FROM trades WHERE ticker != ''"
    params = []
    if account_id:
        sql += " AND account_id = ?"
        params.append(account_id)
    sql += " ORDER BY ticker"

    with connect() as db:
        return [row["ticker"] for row in db.execute(sql, params)]


def get_setting(key):
    with connect() as db:
        row = db.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None


def save_setting(key, value):
    with connect() as db:
        db.execute(
            "INSERT INTO settings VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


def delete_setting(key):
    with connect() as db:
        db.execute("DELETE FROM settings WHERE key = ?", (key,))


def get_position_notes(position_ids):
    if not position_ids:
        return {}

    placeholders = ", ".join("?" for _ in position_ids)
    sql = f"""
        SELECT position_id, entry_note, exit_note
        FROM position_notes
        WHERE position_id IN ({placeholders})
    """
    with connect() as db:
        return {
            row["position_id"]: {
                "entry_note": row["entry_note"],
                "exit_note": row["exit_note"],
            }
            for row in db.execute(sql, position_ids)
        }


def save_position_notes(position_id, entry_note, exit_note):
    with connect() as db:
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


def get_trades(filters):
    conditions = []
    params = []

    if filters.get("account"):
        conditions.append("trades.account_id = ?")
        params.append(filters["account"])
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
    with connect() as db:
        return [dict(row) for row in db.execute(sql, params)]
