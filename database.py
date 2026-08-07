import sqlite3
from pathlib import Path


DATABASE = Path(__file__).with_name("trade_activity.sqlite3")
def connect():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_database():
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

            CREATE INDEX IF NOT EXISTS trades_date ON trades(executed_at);
            CREATE INDEX IF NOT EXISTS trades_ticker ON trades(ticker);
            """
        )

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
            ON CONFLICT(id) DO UPDATE SET name=excluded.name, type=excluded.type, status=excluded.status
            """,
            values,
        )


def save_trades(trades):
    fields = (
        "account_id", "trade_id", "operation_id", "instrument_uid", "ticker",
        "instrument_name", "side", "quantity", "price", "currency", "commission",
        "commission_currency", "payment", "payment_currency", "executed_at",
    )
    rows = [tuple(trade[field] for field in fields) for trade in trades]
    if not rows:
        return 0

    placeholders = ", ".join("?" for _ in fields)
    updates = ", ".join(f"{field}=excluded.{field}" for field in fields[2:])
    with connect() as db:
        db.executemany(
            f"INSERT INTO trades ({', '.join(fields)}) VALUES ({placeholders}) "
            f"ON CONFLICT(account_id, trade_id) DO UPDATE SET {updates}",
            rows,
        )
    return len(rows)


def accounts():
    with connect() as db:
        return [dict(row) for row in db.execute("SELECT * FROM accounts ORDER BY name")]


def instruments():
    with connect() as db:
        rows = db.execute(
            "SELECT instrument_uid, ticker, instrument_name FROM trades GROUP BY instrument_uid"
        )
        return {
            row["instrument_uid"]: {"ticker": row["ticker"], "name": row["instrument_name"]}
            for row in rows
        }


def tickers(account_id=None):
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


def load_trades(filters):
    where = []
    params = []

    if filters.get("account"):
        where.append("trades.account_id = ?")
        params.append(filters["account"])
    if filters.get("search"):
        where.append("(ticker LIKE ? OR instrument_name LIKE ?)")
        query = f"%{filters['search']}%"
        params.extend((query, query))

    clause = f"WHERE {' AND '.join(where)}" if where else ""
    sql = f"""
        SELECT trades.*, accounts.name AS account_name
        FROM trades JOIN accounts ON accounts.id = trades.account_id
        {clause}
    """
    with connect() as db:
        return [dict(row) for row in db.execute(sql, params)]
