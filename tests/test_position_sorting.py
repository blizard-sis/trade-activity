import unittest
from unittest.mock import patch

from backend import create_app
from backend.domain.analytics import sort_positions


class PositionSortingTests(unittest.TestCase):
    def test_numeric_columns_sort_numerically_with_missing_values_last(self):
        fields = {
            "quantity": "entry_quantity",
            "remaining": "remaining",
            "entry": "entry_price",
            "exit_price": "exit_price",
            "gross_result": "gross_result",
            "commission": "commission",
            "net_result": "net_result",
            "order_count": "order_count",
        }
        for sort, field in fields.items():
            rows = [{"id": str(value), field: value} for value in (20, None, -10, 2, 0)]
            for direction, expected in (
                ("asc", ["-10", "0", "2", "20", "None"]),
                ("desc", ["20", "2", "0", "-10", "None"]),
            ):
                with self.subTest(sort=sort, direction=direction):
                    result = sort_positions(rows, {"sort": sort, "direction_sort": direction})
                    self.assertEqual([row["id"] for row in result], expected)

    def test_date_columns_keep_open_positions_last_in_both_directions(self):
        for sort, field in (("date", "entry_at"), ("exit", "exit_at")):
            rows = [
                {"id": "late", field: "2026-09-29T12:00:00"},
                {"id": "missing", field: None},
                {"id": "early", field: "2026-09-28T12:00:00"},
            ]
            for direction, expected in (
                ("asc", ["early", "late", "missing"]),
                ("desc", ["late", "early", "missing"]),
            ):
                with self.subTest(sort=sort, direction=direction):
                    result = sort_positions(rows, {"sort": sort, "direction_sort": direction})
                    self.assertEqual([row["id"] for row in result], expected)

    def test_text_columns_ignore_case_and_use_displayed_instrument_name(self):
        for sort, field in (
            ("account", "account_name"),
            ("ticker", "ticker"),
            ("direction", "direction"),
            ("status", "status"),
        ):
            rows = [{"id": "z", field: "Z"}, {"id": "a", field: "a"}]
            with self.subTest(sort=sort):
                result = sort_positions(rows, {"sort": sort, "direction_sort": "asc"})
                self.assertEqual([row["id"] for row in result], ["a", "z"])
        rows = [
            {"id": "z", "ticker": "Z"},
            {"id": "a", "ticker": "", "instrument_name": "Alpha"},
        ]
        result = sort_positions(rows, {"sort": "ticker", "direction_sort": "asc"})
        self.assertEqual([row["id"] for row in result], ["a", "z"])

    def test_unknown_sort_keeps_default_entry_date_order(self):
        rows = [{"entry_at": "2026-09-28"}, {"entry_at": "2026-09-29"}]
        self.assertEqual(sort_positions(rows, {"sort": "invalid"}), list(reversed(rows)))

    def test_api_sorts_exit_reason_after_loading_journal_plan(self):
        with patch("backend.database.initialize"), patch("backend.load_config", return_value={}):
            client = create_app().test_client()
        rows = [
            {"id": reason, "status": "closed", "direction": "long", "exit_prices": [price]}
            for reason, price in (("take", 110), ("stop", 90), ("unknown", 100), ("manual", 100))
        ]
        notes = {
            reason: {"planned_stop": "95", "planned_take": "105"}
            for reason in ("take", "stop", "manual")
        }
        with (
            patch(
                "backend.services.journal.get_positions",
                side_effect=lambda filters: [dict(row) for row in rows],
            ),
            patch("backend.services.journal.database.get_position_notes", return_value=notes),
        ):
            for direction, expected in (
                ("asc", ["manual", "unknown", "stop", "take"]),
                ("desc", ["take", "stop", "unknown", "manual"]),
            ):
                response = client.get(f"/api/positions?sort=exit_reason&direction_sort={direction}")
                self.assertEqual(response.status_code, 200)
                self.assertEqual([row["id"] for row in response.get_json()], expected)
