import unittest

from backend.domain.analytics import monthly_report
from backend.domain.winrate import win_rates
import test_journal


class WinRateTests(unittest.TestCase):
    def position(self, price, net, **changes):
        return dict(status='closed', ticker='TEST', direction='long', exit_at='2026-09-01',
                    result_currency='USD', net_result=net, gross_result=net, commission=0,
                    planned_stop='95', planned_take='110', exit_prices=[price]) | changes

    def test_counts_by_exit_not_profit_and_excludes_open(self):
        rows = [self.position(110, -1), self.position(95, 1),
                self.position(100, 1), self.position(100, 0),
                self.position(100, -1, exit_prices=[95, 110]),
                self.position(110, 1, planned_stop='', planned_take=''),
                self.position(110, 1, status='open')]
        report = monthly_report(rows, {})[0]
        self.assertEqual(report['positions'], 6)
        self.assertEqual(report['win_rate'], 50)
        self.assertEqual(report['clean_win_rate'], 50)
        self.assertEqual([report[k] for k in ('takes', 'stops', 'manual', 'mixed', 'unknown')], [1, 1, 2, 1, 1])

    def test_empty_sample_is_not_zero_percent(self):
        self.assertIsNone(win_rates(0, 0, 0, 0)['win_rate'])
        report = monthly_report([self.position(100, 1)], {})[0]
        self.assertEqual(report['win_rate'], 100)
        self.assertIsNone(report['clean_win_rate'])


class WinRateIntegrationTests(unittest.TestCase):
    setUp = test_journal.JournalTests.setUp

    def test_saved_plan_changes_clean_rate_and_export(self):
        before = self.client.get('/api/monthly').get_json()[0]
        self.assertEqual(before['win_rate'], 100)
        self.assertIsNone(before['clean_win_rate'])
        self.client.put('/api/journal/' + self.position_id, json={'planned_stop': '95', 'planned_take': '110'})
        after = self.client.get('/api/monthly').get_json()[0]
        self.assertEqual(after['clean_win_rate'], 100)
        self.assertEqual(after['takes'], 1)
        summary = self.client.get('/api/positions/export').get_json()['summary']
        self.assertEqual(summary['clean_win_rate_percent'], 100)
        self.assertEqual(summary['win_rate_percent'], 100)
