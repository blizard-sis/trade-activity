"""Persistent catalog snapshots and user-defined forecast/execution links."""

import json
import sqlite3

from .database import transaction


def save_instruments(instruments):
    with transaction() as db:
        for item in instruments:
            db.execute(
                "INSERT INTO instrument_catalog VALUES (?, ?, ?) "
                "ON CONFLICT(provider, instrument_id) DO UPDATE SET payload=excluded.payload",
                (item["provider"], item["id"], json.dumps(item, ensure_ascii=False)),
            )


def get_instrument(provider, instrument_id):
    with transaction() as db:
        row = db.execute(
            "SELECT payload FROM instrument_catalog WHERE provider=? AND instrument_id=?",
            (provider, instrument_id),
        ).fetchone()
        return json.loads(row["payload"]) if row else None


LINK_QUERY = """
    SELECT links.id, forecast.payload AS forecast, execution.payload AS execution
    FROM instrument_links AS links
    JOIN instrument_catalog AS forecast
      ON forecast.provider = links.forecast_provider
      AND forecast.instrument_id = links.forecast_id
    JOIN instrument_catalog AS execution
      ON execution.provider = links.execution_provider
      AND execution.instrument_id = links.execution_id
"""


def _decode_link(row):
    return {
        "id": row["id"],
        "forecast": json.loads(row["forecast"]),
        "execution": json.loads(row["execution"]),
    }


def get_links():
    with transaction() as db:
        rows = db.execute(LINK_QUERY + " ORDER BY links.rowid").fetchall()
    return [_decode_link(row) for row in rows]


def get_link(link_id):
    with transaction() as db:
        row = db.execute(LINK_QUERY + " WHERE links.id = ?", (link_id,)).fetchone()
    return _decode_link(row) if row else None


def save_link(link_id, forecast, execution, *, update=False):
    values = (forecast["provider"], forecast["id"], execution["provider"], execution["id"])
    try:
        with transaction() as db:
            if update:
                cursor = db.execute(
                    "UPDATE instrument_links SET forecast_provider=?, forecast_id=?, execution_provider=?, execution_id=? WHERE id=?",
                    (*values, link_id),
                )
                if not cursor.rowcount:
                    raise LookupError("Связка не найдена")
            else:
                db.execute(
                    "INSERT INTO instrument_links VALUES (?, ?, ?, ?, ?)", (link_id, *values)
                )
    except sqlite3.IntegrityError:
        raise ValueError("Такая связка инструментов уже существует") from None


def delete_link(link_id):
    with transaction() as db:
        if not db.execute("DELETE FROM instrument_links WHERE id=?", (link_id,)).rowcount:
            raise LookupError("Связка не найдена")
