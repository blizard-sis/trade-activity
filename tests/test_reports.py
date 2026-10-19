import unittest

import test_journal

from backend.domain.reports import trading_report


def position(day, currency="USD", ticker="BRV6", status="closed"):
    return dict(
        status=status,
        ticker=ticker,
        entry_at="2026-08-01",
        exit_at=f"2026-09-{day:02}T15:00:00",
        result_currency=currency,
        net_result=9,
        gross_result=10,
        commission=1,
        exit_assessment={"reason": "manual", "source": "manual"},
    )


class ReportTests(unittest.TestCase):
    def test_days_use_exit_date_and_keep_currencies_separate(self):
        positions = [
            position(1),
            position(1),
            position(2),
            position(2, "RUB"),
            position(3, status="open"),
        ]
        daily = trading_report(positions, {"group_by": "day"})
        self.assertEqual(
            [row["period"] for row in daily], ["2026-09-02", "2026-09-02", "2026-09-01"]
        )
        self.assertEqual(daily[-1]["positions"], 2)
        self.assertEqual(daily[-1]["net_result"], 18)
        monthly = trading_report(positions, {})
        self.assertEqual(len(monthly), 2)
        self.assertEqual(sum(row["positions"] for row in monthly), 4)

    def test_day_bounds_are_inclusive_and_ticker_filters_apply(self):
        positions = [position(1), position(2), position(3), position(2, ticker="GDZ6")]
        filters = {
            "group_by": "day",
            "period_from": "2026-09-02",
            "period_to": "2026-09-02",
            "ticker": "BR",
            "ticker_mode": "only",
        }
        self.assertEqual(trading_report(positions, filters)[0]["positions"], 1)
        self.assertEqual(
            trading_report(positions, filters | {"ticker_mode": "exclude"})[0]["positions"], 1
        )
        self.assertEqual(trading_report(positions, filters | {"period_from": "2026-10-01"}), [])


class ReportApiTests(unittest.TestCase):
    setUp = test_journal.JournalTests.setUp

    def test_report_api_and_saved_filters(self):
        monthly = self.client.get("/api/monthly").get_json()[0]
        daily = self.client.get("/api/reports/trading?group_by=day").get_json()[0]
        self.assertEqual(daily["period"][:7], monthly["month"])
        self.assertEqual(daily["net_result"], monthly["net_result"])
        self.assertEqual(self.client.get("/api/reports/trading?group_by=week").status_code, 400)
        self.assertEqual(
            self.client.get("/api/reports/trading?group_by=day&account=missing").get_json(), []
        )
        filters = {
            "account": ["one", "two"],
            "group_by": "day",
            "period_from": "2026-09-01",
            "period_to": "2026-09-30",
            "ticker_mode": "exclude",
            "ticker": "BR",
        }
        self.assertEqual(self.client.put("/api/report-filters", json=filters).get_json(), filters)
        self.assertEqual(self.client.get("/api/report-filters").get_json(), filters)
        self.client.delete("/api/report-filters")
        self.assertEqual(self.client.get("/api/report-filters").get_json(), {})
