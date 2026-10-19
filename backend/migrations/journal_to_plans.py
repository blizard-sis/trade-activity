"""Copy the legacy per-position journal into plans without changing old data.

The migration is additive and idempotent:

* one legacy journal row becomes one plan with one linked position;
* ``entry_note``/``exit_note`` and the planned levels are copied verbatim;
* the legacy ``position_notes`` table is never modified;
* no migration event is written, so the new plan has a clean timeline.

Run without ``--apply`` for a dry run. The dry run reads the database and
checks that the mapping preserves note text, levels, exit assessments and the
monthly report. ``--apply`` creates a backup first and verifies everything
inside the same transaction.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from ..domain.journal import assess_exit
from ..domain.numbers import number_or_none
from ..domain.reports import monthly_report
from ..services.journal import get_journal_positions
from ..storage import database

MIGRATION_KEY = "plans_migration_v1"
PLAN_NAMESPACE = uuid5(NAMESPACE_URL, "trade-activity/plans")

PLAN_INSERT = """
    INSERT INTO plans (
        id, title, thesis, review, direction, account_id,
        forecast_provider, forecast_id, forecast_payload,
        execution_provider, execution_id, execution_payload,
        entry_zone, planned_stop, planned_take, planned_for, valid_until,
        parent_plan_id, cover_attachment_id, created_at, updated_at
    ) VALUES (
        :id, :title, :thesis, :review, :direction, :account_id,
        :forecast_provider, :forecast_id, :forecast_payload,
        :execution_provider, :execution_id, :execution_payload,
        :entry_zone, :planned_stop, :planned_take, :planned_for, :valid_until,
        :parent_plan_id, :cover_attachment_id, :created_at, :updated_at
    )
"""

LINK_INSERT = """
    INSERT INTO plan_positions (
        plan_id, position_id, account_id, instrument_uid, entry_trade_id,
        direction, link_source, linked_at, planned_stop_override,
        planned_take_override, stop_at_close, take_at_close, closed_at
    ) VALUES (
        :plan_id, :position_id, :account_id, :instrument_uid, :entry_trade_id,
        :direction, :link_source, :linked_at, :planned_stop_override,
        :planned_take_override, :stop_at_close, :take_at_close, :closed_at
    )
"""


class MigrationVerificationError(RuntimeError):
    def __init__(self, problems):
        super().__init__("; ".join(problems[:3]))
        self.problems = problems


@contextmanager
def use_database(path):
    """Point the storage layer at another SQLite file for the duration."""
    previous = database.DATABASE
    database.DATABASE = Path(path)
    try:
        yield
    finally:
        database.DATABASE = previous


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_positions():
    return {position["id"]: position for position in get_journal_positions({})}


def read_notes(db):
    """Read every legacy column, including fields hidden from the old UI."""
    columns = {row["name"] for row in db.execute("PRAGMA table_info(position_notes)")}
    wanted = (
        "position_id",
        "entry_note",
        "exit_note",
        "updated_at",
        "planned_stop",
        "planned_take",
        "exit_reason",
        "emotions",
        "lessons",
    )
    expressions = [name if name in columns else f"'' AS {name}" for name in wanted]
    rows = db.execute(f"SELECT {', '.join(expressions)} FROM position_notes").fetchall()
    return {row["position_id"]: dict(row) for row in rows}


def load_notes():
    with database.transaction() as db:
        return read_notes(db)


def text(note, key):
    return note.get(key) or ""


def checksums(notes):
    ordered = [notes[position_id] for position_id in sorted(notes)]

    def digest(values):
        return hashlib.sha256("\n".join(values).encode("utf-8")).hexdigest()

    return {
        "ids": digest([note["position_id"] for note in ordered]),
        "entry": digest([text(note, "entry_note") for note in ordered]),
        "exit": digest([text(note, "exit_note") for note in ordered]),
        "levels": digest(
            [f"{text(note, 'planned_stop')}|{text(note, 'planned_take')}" for note in ordered]
        ),
    }


def display_date(value):
    if not value:
        return ""
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).strftime("%d.%m.%Y")
    except ValueError:
        return str(value)[:10]


def execution_snapshot(position):
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
    return (
        provider,
        position["instrument_uid"],
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
    )


def position_entry_trade_id(position):
    value = position.get("entry_trade_id")
    if value:
        return str(value)

    # Older TradingView payloads do not carry the order id separately. The id
    # is account:symbol:order:direction, and the order id is the last segment.
    identifier = position["id"]
    prefix = f"{position['account_id']}:"
    suffix = f":{position['direction']}"
    if identifier.startswith(prefix) and identifier.endswith(suffix):
        middle = identifier[len(prefix) : -len(suffix)]
        return middle.rsplit(":", 1)[-1] if ":" in middle else middle
    return ""


def plan_title(position):
    ticker = position["ticker"] or position["instrument_name"] or "Без тикера"
    direction = "Лонг" if position["direction"] == "long" else "Шорт"
    return f"{ticker} · {direction} · {display_date(position['entry_at'])}"


def build_records(position, note, now):
    plan_id = str(uuid5(PLAN_NAMESPACE, position["id"]))
    closed = position["status"] == "closed"
    provider, execution_id, execution_payload = execution_snapshot(position)
    stop_text = text(note, "planned_stop")
    take_text = text(note, "planned_take")
    stop = number_or_none(stop_text)
    take = number_or_none(take_text)

    plan = {
        "id": plan_id,
        "title": plan_title(position),
        "thesis": text(note, "entry_note"),
        "review": text(note, "exit_note"),
        "direction": position["direction"],
        "account_id": position["account_id"],
        "forecast_provider": None,
        "forecast_id": None,
        "forecast_payload": "{}",
        "execution_provider": provider,
        "execution_id": execution_id,
        "execution_payload": execution_payload,
        "entry_zone": "",
        "planned_stop": stop,
        "planned_take": take,
        "planned_for": None,
        "valid_until": None,
        "parent_plan_id": None,
        "cover_attachment_id": None,
        "created_at": now,
        "updated_at": now,
    }
    link = {
        "plan_id": plan_id,
        "position_id": position["id"],
        "account_id": position["account_id"],
        "instrument_uid": position["instrument_uid"],
        "entry_trade_id": position_entry_trade_id(position),
        "direction": position["direction"],
        "link_source": "manual",
        "linked_at": now,
        "planned_stop_override": "",
        "planned_take_override": "",
        "stop_at_close": stop_text if closed else "",
        "take_at_close": take_text if closed else "",
        "closed_at": position["exit_at"] if closed else None,
    }
    return plan, link


def assessment_key(assessment):
    return "|".join(
        (
            str(assessment.get("reason", "")),
            str(assessment.get("label", "")),
            str(assessment.get("source", "")),
            str(bool(assessment.get("inferred"))),
        )
    )


def compare_assessments(positions, notes, levels):
    before = {}
    after = {}
    mismatches = []
    for position_id in sorted(set(positions) & set(notes)):
        position = positions[position_id]
        stop, take = levels.get(
            position_id,
            (text(notes[position_id], "planned_stop"), text(notes[position_id], "planned_take")),
        )
        current = position.get("exit_assessment") or assess_exit(position)
        mapped = assess_exit({**position, "planned_stop": stop, "planned_take": take})
        current_key = assessment_key(current)
        mapped_key = assessment_key(mapped)
        before[current_key] = before.get(current_key, 0) + 1
        after[mapped_key] = after.get(mapped_key, 0) + 1
        if current_key != mapped_key:
            mismatches.append({"position_id": position_id, "before": current, "after": mapped})
    return {
        "before": dict(sorted(before.items())),
        "after": dict(sorted(after.items())),
        "mismatches": mismatches[:20],
        "mismatch_count": len(mismatches),
    }


def monthly_snapshot(positions, levels):
    rows = []
    for position_id, position in positions.items():
        stop, take = levels.get(
            position_id, (position.get("planned_stop") or "", position.get("planned_take") or "")
        )
        rows.append({**position, "planned_stop": stop, "planned_take": take})
    return monthly_report(rows, {})


def dry_run_verification(positions, notes, matched, checksums_before, planned_levels):
    assessment = compare_assessments(positions, notes, planned_levels)
    before_monthly = monthly_snapshot(
        positions,
        {
            position_id: (
                text(notes[position_id], "planned_stop"),
                text(notes[position_id], "planned_take"),
            )
            for position_id in matched
        },
    )
    after_monthly = monthly_snapshot(positions, planned_levels)
    problems = []
    for position_id in matched:
        expected = (
            number_or_none(text(notes[position_id], "planned_stop")),
            number_or_none(text(notes[position_id], "planned_take")),
        )
        if planned_levels.get(position_id) != expected:
            problems.append(f"{position_id}: уровни плана не совпадают со старым дневником")
    if assessment["mismatches"]:
        problems.append("Оценки выхода расходятся после переноса уровней")
    if before_monthly != after_monthly:
        problems.append("Помесячный отчёт расходится после переноса уровней")
    return {
        "ok": not problems,
        "problems": problems[:50],
        "would_create": len(matched),
        "assessment": assessment,
        "monthly_equal": before_monthly == after_monthly,
        "checksums_match": checksums(notes) == checksums_before,
    }


def verify_db(db, positions, notes, checksums_before):
    problems = []
    matched = sorted(set(positions) & set(notes))
    rows = []
    if matched:
        placeholders = ", ".join("?" for _ in matched)
        rows = db.execute(
            f"""
            SELECT plans.*, links.position_id AS linked_position_id,
                   links.stop_at_close, links.take_at_close, links.closed_at
            FROM plans
            JOIN plan_positions AS links ON links.plan_id = plans.id
            WHERE links.position_id IN ({placeholders})
            """,
            matched,
        ).fetchall()
    by_position = {row["linked_position_id"]: dict(row) for row in rows}

    plan_count = len(by_position)
    link_count = len(rows)

    levels = {}
    for position_id in matched:
        row = by_position.get(position_id)
        if row is None:
            problems.append(f"Нет плана для позиции {position_id}")
            continue
        note = notes[position_id]
        position = positions[position_id]
        for actual, expected, label in (
            (row["thesis"], text(note, "entry_note"), "entry_note"),
            (row["review"], text(note, "exit_note"), "exit_note"),
            (row["planned_stop"], number_or_none(text(note, "planned_stop")), "planned_stop"),
            (row["planned_take"], number_or_none(text(note, "planned_take")), "planned_take"),
            (row["direction"], position["direction"], "direction"),
            (row["account_id"], position["account_id"], "account_id"),
        ):
            if actual != expected:
                problems.append(f"{position_id}: {label} не совпадает")
        if position["status"] == "closed":
            if row["stop_at_close"] != text(note, "planned_stop"):
                problems.append(f"{position_id}: stop_at_close не совпадает")
            if row["take_at_close"] != text(note, "planned_take"):
                problems.append(f"{position_id}: take_at_close не совпадает")
            if row["closed_at"] != position["exit_at"]:
                problems.append(f"{position_id}: closed_at не совпадает")
        levels[position_id] = (row["planned_stop"], row["planned_take"])

    duplicates = db.execute(
        """
        SELECT position_id, COUNT(*) AS copies
        FROM plan_positions
        GROUP BY position_id
        HAVING copies > 1
        """
    ).fetchall()
    for row in duplicates:
        problems.append(f"{row['position_id']}: привязан к нескольким планам")

    notes_after = read_notes(db)
    checksums_after = checksums(notes_after)
    if len(notes_after) != len(notes):
        problems.append(f"Записей старого дневника {len(notes_after)}, было {len(notes)}")
    if checksums_after != checksums_before:
        problems.append("Контрольные суммы старого дневника изменились")

    assessment = compare_assessments(positions, notes, levels)
    if assessment["mismatch_count"]:
        problems.append(f"Оценки выхода расходятся: {assessment['mismatch_count']}")

    before_monthly = monthly_snapshot(
        positions,
        {
            position_id: (
                text(notes[position_id], "planned_stop"),
                text(notes[position_id], "planned_take"),
            )
            for position_id in matched
        },
    )
    after_monthly = monthly_snapshot(positions, levels)
    monthly_equal = before_monthly == after_monthly
    if not monthly_equal:
        problems.append("Помесячный отчёт до и после расходится")

    integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        problems.append(f"SQLite integrity_check: {integrity}")

    return {
        "ok": not problems,
        "problems": problems[:50],
        "plans": plan_count,
        "links": link_count,
        "notes": len(notes_after),
        "checksums_match": checksums_after == checksums_before,
        "assessment": assessment,
        "monthly_equal": monthly_equal,
        "integrity": integrity,
    }


def is_already_applied(path):
    """Read the migration marker without touching the database file."""
    connection = sqlite3.connect(path)
    try:
        connection.execute("PRAGMA query_only = ON")
        row = connection.execute(
            "SELECT 1 FROM settings WHERE key = ?", (MIGRATION_KEY,)
        ).fetchone()
        return bool(row)
    except sqlite3.Error:
        # An old database may not have the settings table yet.
        return False
    finally:
        connection.close()


def backup_database(path):
    path = Path(path)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(f"{path.name}.bak-{timestamp}")
    counter = 1
    while backup.exists():
        backup = path.with_name(f"{path.name}.bak-{timestamp}-{counter}")
        counter += 1

    source = sqlite3.connect(path)
    target = sqlite3.connect(backup)
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()
    try:
        backup.chmod(0o600)
    except OSError:
        # Windows does not implement POSIX permissions; the backup is still valid.
        pass

    check = sqlite3.connect(backup)
    try:
        result = check.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        check.close()
    if result != "ok":
        raise RuntimeError(f"Резервная копия повреждена: {result}")
    return backup


def migrate(database_path, *, apply=False):
    path = Path(database_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(path)

    before_hash = file_sha256(path)
    report = {
        "database": str(path),
        "mode": "apply" if apply else "dry-run",
        "notes": 0,
        "positions": 0,
        "matched": 0,
        "orphans": [],
        "plans_would_create": 0,
        "plans_created": 0,
        "skipped_existing": 0,
        "already_applied": False,
        "backup": None,
        "checksums": {},
        "verification": {},
        "database_sha256_before": before_hash,
    }

    already_applied = apply and is_already_applied(path)
    if apply and not already_applied:
        report["backup"] = str(backup_database(path))

    with use_database(path):
        if apply:
            database.initialize()
        positions = load_positions()
        notes = load_notes()
        matched = sorted(set(positions) & set(notes))
        orphans = sorted(set(notes) - set(positions))
        checksums_before = checksums(notes)
        report.update(
            notes=len(notes),
            positions=len(positions),
            matched=len(matched),
            orphans=orphans,
            plans_would_create=len(matched),
            checksums=checksums_before,
        )

        now = datetime.now(timezone.utc).isoformat()
        records = [
            build_records(positions[position_id], notes[position_id], now)
            for position_id in matched
        ]
        planned_levels = {
            link["position_id"]: (plan["planned_stop"], plan["planned_take"])
            for plan, link in records
        }

        if not apply:
            report["verification"] = dry_run_verification(
                positions, notes, matched, checksums_before, planned_levels
            )
            report["database_sha256_after"] = file_sha256(path)
            report["database_unchanged"] = report["database_sha256_after"] == before_hash
            return report

        created = 0
        skipped = 0
        try:
            with database.transaction() as db:
                marker = db.execute(
                    "SELECT value FROM settings WHERE key = ?", (MIGRATION_KEY,)
                ).fetchone()
                if marker:
                    report["already_applied"] = True
                    verification = verify_db(db, positions, notes, checksums_before)
                else:
                    for plan, link in records:
                        if db.execute("SELECT 1 FROM plans WHERE id = ?", (plan["id"],)).fetchone():
                            skipped += 1
                            continue
                        db.execute(PLAN_INSERT, plan)
                        db.execute(LINK_INSERT, link)
                        created += 1

                    verification = verify_db(db, positions, notes, checksums_before)
                    if not verification["ok"]:
                        raise MigrationVerificationError(verification["problems"])
                    db.execute(
                        "INSERT INTO settings (key, value) VALUES (?, ?) "
                        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                        (
                            MIGRATION_KEY,
                            json.dumps(
                                {
                                    "version": 1,
                                    "applied_at": now,
                                    "notes": len(notes),
                                    "matched": len(matched),
                                    "plans": created,
                                    "checksums": checksums_before,
                                },
                                ensure_ascii=False,
                                sort_keys=True,
                            ),
                        ),
                    )
        except MigrationVerificationError as error:
            report["error"] = "Проверка не пройдена, изменения откатаны"
            report["verification"] = {"ok": False, "problems": error.problems}
            report["plans_created"] = 0
            report["database_sha256_after"] = file_sha256(path)
            return report
        except sqlite3.Error as error:
            report["error"] = f"Ошибка SQLite: {error}"
            report["verification"] = {"ok": False, "problems": [report["error"]]}
            report["plans_created"] = 0
            report["database_sha256_after"] = file_sha256(path)
            return report

        report["plans_created"] = created
        report["skipped_existing"] = skipped
        report["verification"] = verification
        report["database_sha256_after"] = file_sha256(path)
        return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database",
        default=str(database.DATABASE),
        help="SQLite file to migrate (default: the local trade_activity.sqlite3)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--apply",
        action="store_true",
        help="write the plans; without this flag the command only checks the mapping",
    )
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="explicitly request the read-only check (the default)",
    )
    args = parser.parse_args(argv)

    try:
        report = migrate(args.database, apply=args.apply)
    except Exception as error:  # noqa: BLE001 - the CLI must report, not traceback.
        report = {"ok": False, "error": str(error)}

    print(json.dumps(report, ensure_ascii=False, indent=2))
    verification = report.get("verification") or {}
    return 0 if verification.get("ok") and not report.get("error") else 1


if __name__ == "__main__":
    raise SystemExit(main())
