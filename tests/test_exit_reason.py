import unittest

from backend.domain.journal import assess_exit


class ExitReasonTests(unittest.TestCase):
    def assess(self, **changes):
        values = dict(
            status="closed",
            direction="long",
            planned_entry="100",
            entry_price="100",
            planned_stop="95",
            planned_take="110",
            exit_prices=[100],
        )
        values.update(changes)
        return assess_exit(values)

    def test_long_and_short_levels_and_slippage(self):
        for direction, stop, take, prices, expected in (
            ("long", "95", "110", [95, 94.5], "stop"),
            ("long", "95", "110", [110, 111], "take"),
            ("long", "95", "110", [100, 103], "manual"),
            ("short", "110", "95", [110, 111], "stop"),
            ("short", "110", "95", [95, 94.5], "take"),
            ("short", "110", "95", [100, 103], "manual"),
        ):
            with self.subTest(direction=direction, prices=prices):
                result = self.assess(
                    direction=direction, planned_stop=stop, planned_take=take, exit_prices=prices
                )
                self.assertEqual(result["reason"], expected)
                self.assertTrue(result["inferred"])

    def test_mixed_fills_not_average(self):
        self.assertEqual(self.assess(exit_prices=[94, 111])["reason"], "mixed")

    def test_manual_default_without_both_levels(self):
        result = self.assess(planned_take="")
        self.assertEqual(result["reason"], "manual")
        self.assertEqual(result["label"], "Вышел руками")
        self.assertEqual(self.assess(planned_stop="")["reason"], "manual")
        both_missing = self.assess(planned_stop="", planned_take="")
        self.assertEqual(both_missing["reason"], "manual")
        self.assertEqual(both_missing["source"], "default_rule")
        self.assertEqual(self.assess(planned_take="", exit_prices=[94])["reason"], "stop")

    def test_open_invalid_or_missing_data(self):
        self.assertEqual(self.assess(status="open", exit_prices=[94])["reason"], "open")
        for changes in (
            {"planned_stop": "120"},
            {"exit_prices": []},
            {"exit_prices": [None]},
            {"planned_stop": "NaN", "planned_take": "abc"},
            {"entry_price": ""},
        ):
            with self.subTest(changes=changes):
                self.assertEqual(self.assess(**changes)["reason"], "manual")

    def test_decimal_comma(self):
        self.assertEqual(self.assess(planned_stop="95,5", exit_prices=[95.5])["reason"], "stop")

    def test_short_stop_with_grouping_spaces_and_no_take(self):
        for separator in (" ", "\u00a0", "\u202f"):
            with self.subTest(separator=repr(separator)):
                result = self.assess(
                    direction="short",
                    planned_entry="214500",
                    entry_price="214500",
                    planned_stop=f"214{separator}550",
                    planned_take="",
                    exit_prices=[214563],
                )
                self.assertEqual(result["reason"], "stop")
                self.assertEqual(result["source"], "plan_prices")

    def test_grouped_decimal_take(self):
        result = self.assess(
            direction="long",
            planned_entry="210500",
            entry_price="210500",
            planned_stop="",
            planned_take="210 500,5",
            exit_prices=[210500.5],
        )
        self.assertEqual(result["reason"], "take")

    def test_uses_actual_entry_not_absolute_plan_levels(self):
        result = self.assess(
            planned_entry="57.11",
            entry_price="57.755",
            planned_stop="56.91",
            planned_take="57.71",
            exit_prices=[57.83],
        )
        self.assertEqual(result["reason"], "manual")
        self.assertEqual(result["label"], "Вышел руками")

        self.assertEqual(
            self.assess(
                planned_entry="57.11",
                entry_price="57.755",
                planned_stop="56.91",
                planned_take="57.71",
                exit_prices=[58.34],
            )["reason"],
            "take",
        )
        self.assertEqual(
            self.assess(
                planned_entry="57.11",
                entry_price="57.755",
                planned_stop="56.91",
                planned_take="57.71",
                exit_prices=[57.575],
            )["reason"],
            "stop",
        )

    def test_two_tick_tolerance(self):
        self.assertEqual(
            self.assess(
                planned_entry="100.00",
                entry_price="100.00",
                planned_stop="95.00",
                planned_take="110.00",
                exit_prices=[109.99],
            )["reason"],
            "take",
        )
        self.assertEqual(
            self.assess(
                planned_entry="100.00",
                entry_price="100.00",
                planned_stop="95.00",
                planned_take="110.00",
                exit_prices=[109.97],
            )["reason"],
            "manual",
        )
        self.assertEqual(
            self.assess(
                planned_entry="100.00",
                entry_price="100.00",
                planned_stop="95.00",
                planned_take="110.00",
                exit_prices=[95.01],
            )["reason"],
            "stop",
        )

    def test_legacy_without_planned_entry_uses_actual_entry(self):
        result = self.assess(planned_entry="", entry_price="100", exit_prices=[95])
        self.assertEqual(result["reason"], "stop")


if __name__ == "__main__":
    unittest.main()
