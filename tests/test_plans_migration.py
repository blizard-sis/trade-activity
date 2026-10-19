import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.migrations import journal_to_plans as migration
from backend.storage import database


class PlansMigrationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / "journal.sqlite3"
        db_patch = patch.object(database, "DATABASE", self.path)
        db_patch.start()
        self.addCleanup(db_patch.stop)

        database.initialize()
        database.save_account({"id": "a", "name": "Test account"})
        # Mirror the real database, which still has columns hidden from the UI.
        with database.transaction() as db:
            for name in ("exit_reason", "emotions", "lessons"):
                db.execute(f"ALTER TABLE position_notes ADD COLUMN {name} TEXT NOT NULL DEFAULT ''")

        database.save_trades(
            [
                self.trade("buy", "instrument", "buy", 100, -100, "2026-09-01T10:00:00Z"),
                self.trade("sell", "instrument", "sell", 110, 110, "2026-09-02T10:00:00Z"),
                self.trade("sell2", "instrument2", "sell", 200, 200, "2026-09-03T10:00:00Z"),
                self.trade("buy3", "instrument3", "buy", 50, -50, "2026-09-04T10:00:00Z"),
                self.trade("sell3", "instrument3", "sell", 55, 55, "2026-09-05T10:00:00Z"),
            ]
        )

        self.closed_id = "a:instrument:buy:long"
        self.open_id = "a:instrument2:sell2:short"
        with database.transaction() as db:
            db.execute(
                "INSERT INTO position_notes "
                "(position_id, entry_note, exit_note, updated_at, planned_stop, planned_take, "
                "exit_reason, emotions, lessons) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    self.closed_id,
                    "  Причины входа: пробой  ",
                    "Вышел по тейку",
                    "2026-10-18 12:00:00",
                    "95,5",
                    "110",
                    "take",
                    "  спокоен  ",
                    "ждать",
                ),
            )
            db.execute(
                "INSERT INTO position_notes "
                "(position_id, entry_note, exit_note, updated_at, planned_stop, planned_take, "
                "exit_reason, emotions, lessons) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (self.open_id, "Шорт от 200", "", "2026-10-19 09:30:00", "210", "180", "", "", ""),
            )

    @staticmethod
    def trade(trade_id, instrument_uid, side, price, payment, executed_at):
        trade = dict.fromkeys(database.TRADE_FIELDS, "")
        trade.update(
            account_id="a",
            trade_id=trade_id,
            operation_id=trade_id,
            instrument_uid=instrument_uid,
            ticker=instrument_uid.upper(),
            instrument_name=f"Instrument {instrument_uid}",
            side=side,
            quantity=1,
            price=price,
            currency="rub",
            commission=1,
            commission_currency="rub",
            payment=payment,
            payment_currency="rub",
            executed_at=executed_at,
        )
        return trade

    def plans(self):
        with database.transaction() as db:
            return [
                dict(row)
                for row in db.execute(
                    """
                    SELECT plans.*, links.position_id AS linked_position_id,
                           links.stop_at_close, links.take_at_close, links.closed_at
                    FROM plans
                    JOIN plan_positions AS links ON links.plan_id = plans.id
                    ORDER BY links.position_id
                    """
                )
            ]

    def test_dry_run_does_not_touch_database_and_preserves_statistics(self):
        before = migration.file_sha256(self.path)
        report = migration.migrate(self.path)

        self.assertEqual(report["mode"], "dry-run")
        self.assertEqual((report["notes"], report["matched"], report["orphans"]), (2, 2, []))
        self.assertEqual(report["plans_would_create"], 2)
        self.assertEqual(report["plans_created"], 0)
        self.assertTrue(report["verification"]["ok"])
        self.assertEqual(report["verification"]["assessment"]["mismatch_count"], 0)
        self.assertTrue(report["verification"]["monthly_equal"])
        self.assertTrue(report["database_unchanged"])
        self.assertEqual(migration.file_sha256(self.path), before)
        with database.transaction() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM plans").fetchone()[0], 0)

    def test_apply_preserves_text_levels_statistics_and_marks_the_migration(self):
        report = migration.migrate(self.path, apply=True)

        self.assertEqual(report["plans_created"], 2)
        self.assertEqual(report["skipped_existing"], 0)
        self.assertFalse(report["already_applied"])
        self.assertTrue(report["verification"]["ok"], report["verification"]["problems"])
        self.assertEqual(report["verification"]["plans"], 2)
        self.assertEqual(report["verification"]["links"], 2)
        self.assertTrue(Path(report["backup"]).is_file())

        by_position = {row["linked_position_id"]: row for row in self.plans()}
        closed = by_position[self.closed_id]
        opened = by_position[self.open_id]
        self.assertEqual(closed["thesis"], "  Причины входа: пробой  ")
        self.assertEqual(closed["review"], "Вышел по тейку")
        self.assertEqual(closed["planned_stop"], 95.5)
        self.assertEqual(closed["planned_take"], 110.0)
        self.assertEqual(closed["stop_at_close"], "95,5")
        self.assertEqual(closed["take_at_close"], "110")
        self.assertEqual(closed["closed_at"], "2026-09-02T10:00:00Z")
        self.assertEqual(closed["direction"], "long")
        self.assertEqual(closed["account_id"], "a")
        self.assertEqual(closed["execution_provider"], "tbank")
        self.assertIsNone(closed["forecast_provider"])

        self.assertEqual(opened["review"], "")
        self.assertEqual(opened["stop_at_close"], "")
        self.assertIsNone(opened["closed_at"])

        with database.transaction() as db:
            notes = {
                row["position_id"]: dict(row) for row in db.execute("SELECT * FROM position_notes")
            }
        self.assertEqual(notes[self.closed_id]["entry_note"], "  Причины входа: пробой  ")
        self.assertEqual(notes[self.closed_id]["planned_stop"], "95,5")
        self.assertEqual(notes[self.closed_id]["emotions"], "  спокоен  ")
        self.assertEqual(notes[self.closed_id]["lessons"], "ждать")
        self.assertEqual(len(notes), 2)

    def test_second_apply_is_idempotent_and_does_not_make_another_backup(self):
        first = migration.migrate(self.path, apply=True)
        second = migration.migrate(self.path, apply=True)

        self.assertEqual(first["plans_created"], 2)
        self.assertEqual(second["plans_created"], 0)
        self.assertTrue(second["already_applied"])
        self.assertIsNone(second["backup"])
        self.assertTrue(second["verification"]["ok"], second["verification"]["problems"])
        with database.transaction() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM plans").fetchone()[0], 2)

    def test_orphan_note_is_reported_and_kept(self):
        with database.transaction() as db:
            db.execute(
                "INSERT INTO position_notes (position_id, entry_note, updated_at) VALUES (?, ?, ?)",
                ("missing:position", "Нет такой позиции", "2026-10-18 12:00:00"),
            )

        report = migration.migrate(self.path, apply=True)

        self.assertEqual(report["matched"], 2)
        self.assertEqual(report["orphans"], ["missing:position"])
        self.assertEqual(report["plans_created"], 2)
        self.assertTrue(report["verification"]["ok"], report["verification"]["problems"])
        with database.transaction() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM position_notes").fetchone()[0], 3)
            self.assertEqual(
                db.execute(
                    "SELECT COUNT(*) FROM position_notes WHERE position_id = 'missing:position'"
                ).fetchone()[0],
                1,
            )

    def test_backup_is_readable_and_contains_the_original_notes(self):
        report = migration.migrate(self.path, apply=True)
        backup = Path(report["backup"])

        connection = sqlite3.connect(backup)
        try:
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM position_notes").fetchone()[0], 2
            )
        finally:
            connection.close()

    def test_tradingview_order_id_is_derived_without_parsing_the_whole_id(self):
        position = {
            "id": "tradingview:abc:RUS:MXU2026:3459943666:short",
            "account_id": "tradingview:abc",
            "direction": "short",
            "entry_trade_id": "",
            "instrument_uid": "tradingview:RUS:MXU2026",
            "ticker": "RUS:MXU2026",
            "instrument_name": "RUS:MXU2026",
            "currency": "RUB",
            "price_precision": 9,
            "platform": "TradingView",
        }
        self.assertEqual(migration.position_entry_trade_id(position), "3459943666")
        provider, instrument_id, payload = migration.execution_snapshot(position)
        self.assertEqual(provider, "tradingview")
        self.assertEqual(instrument_id, "tradingview:RUS:MXU2026")
        self.assertEqual(json.loads(payload)["platform"], "TradingView")


if __name__ == "__main__":
    unittest.main()
