import csv
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend import create_app
from backend.storage import database


def report(open_position=False, invalid=False):
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(['Symbol', 'Trade number', 'Type', 'Date and time', 'Order ID', 'Price', 'Size (qty)', 'Net PnL USD', 'Commission USD'])
    writer.writerow(['TEST:FUT', '1', 'Entry short', 'Sep 1, 2026, 10:00', '100', '20', '0.5', '5', '1'])
    writer.writerow(['TEST:FUT', '1', 'Exit short', 'Open' if open_position else 'Sep 2, 2026, 10:00', '' if open_position else '101', '—' if open_position else '19', 'nan' if invalid else '0.5', '0' if open_position else '5', '1'])
    return stream.getvalue().encode()


class TradingViewTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        db_patch = patch.object(database, 'DATABASE', Path(temp.name) / 'db.sqlite')
        db_patch.start()
        self.addCleanup(db_patch.stop)
        with patch('backend.load_config', return_value={}):
            self.client = create_app().test_client()

    def upload(self, content=None, name='Paper Trading'):
        return self.client.post('/api/imports/tradingview', data={
            'account_name': name, 'files': (io.BytesIO(content or report()), 'history.csv'),
        })

    def test_roundtrip_dedup_journal_and_report(self):
        self.assertEqual(self.upload().get_json()['added'], 1)
        position = self.client.get('/api/positions').get_json()[0]
        self.assertEqual(position['net_result'], 5)
        self.assertEqual(position['gross_result'], 6)
        self.assertEqual(position['entry_quantity'], 0.5)
        self.assertEqual(position['direction'], 'short')
        self.client.put('/api/journal/' + position['id'], json={'entry_note': 'Keep me'})
        self.assertEqual(self.upload().get_json()['unchanged'], 1)
        self.assertEqual(self.client.get('/api/journal').get_json()[0]['entry_note'], 'Keep me')
        self.assertEqual(self.client.get('/api/monthly').get_json()[0]['currency'], 'USD')
        self.assertEqual(self.client.get('/api/positions/export').status_code, 200)
        self.assertIn('TEST:FUT', self.client.get('/api/tickers').get_json())

    def test_open_becomes_closed_and_old_export_cannot_reopen(self):
        self.upload(report(open_position=True))
        before = self.client.get('/api/positions').get_json()[0]
        self.assertIsNone(before['net_result'])
        self.assertEqual(self.upload().get_json()['updated'], 1)
        self.assertEqual(self.upload(report(open_position=True)).get_json()['unchanged'], 1)
        after = self.client.get('/api/positions').get_json()[0]
        self.assertEqual(before['id'], after['id'])
        self.assertEqual(after['status'], 'closed')

    def test_bad_file_writes_nothing_and_accounts_are_separate(self):
        self.assertEqual(self.upload(report(invalid=True)).status_code, 400)
        self.assertEqual(database.get_accounts(), [])
        self.assertEqual(self.upload(b'Time,Text\n2026-01-01,hello').status_code, 400)
        self.upload()
        other = self.upload(name='Second').get_json()
        self.assertEqual(other['added'], 1)
        self.assertEqual(len(self.client.get('/api/positions').get_json()), 2)
        self.assertEqual(len(self.client.get('/api/positions?account=' + other['account_id']).get_json()), 1)

    def test_monthly_does_not_add_different_currencies(self):
        from backend.domain.analytics import monthly_report
        base = dict(status='closed', ticker='TEST', exit_at='2026-09-02', net_result=5, gross_result=6, commission=1)
        rows = monthly_report([{**base, 'result_currency': 'usd'}, {**base, 'result_currency': 'rub'}], {})
        self.assertEqual(len(rows), 2)
        self.assertEqual({r['currency'] for r in rows}, {'USD', 'RUB'})
        self.assertTrue(all(r['net_result'] == 5 for r in rows))

    def test_multiple_accounts_filters_and_saved_selection(self):
        from urllib.parse import urlencode
        first = self.upload().get_json()['account_id']
        second = self.upload(name='Second').get_json()['account_id']
        self.upload(name='Excluded')
        query = urlencode([('account', first), ('account', second)])
        positions = self.client.get('/api/positions?' + query).get_json()
        self.assertEqual({p['account_id'] for p in positions}, {first, second})
        self.assertTrue(all(p['account_name'].startswith('TradingView — ') for p in positions))
        self.assertEqual(self.client.get('/api/monthly?' + query).get_json()[0]['positions'], 2)
        exported = self.client.get('/api/positions/export?' + query).get_json()
        self.assertEqual(exported['filters']['account'], [first, second])
        self.assertEqual(len(exported['positions']), 2)
        self.client.put('/api/monthly-filters', json={'account': [first, second]})
        self.assertEqual(self.client.get('/api/monthly-filters').get_json()['account'], [first, second])

    def test_journal_column_migrates_and_can_stay_hidden(self):
        database.save_setting('position_table_settings', '{"visible_columns": ["entry_at"]}')
        self.assertEqual(self.client.get('/api/position-table-settings').get_json()['visible_columns'], ['entry_at', 'journal'])
        self.client.put('/api/position-table-settings', json={'visible_columns': ['entry_at']})
        self.assertEqual(self.client.get('/api/position-table-settings').get_json()['visible_columns'], ['entry_at'])
        self.client.put('/api/position-table-settings', json={'visible_columns': ['entry_at', 'journal']})
        self.assertIn('journal', self.client.get('/api/position-table-settings').get_json()['visible_columns'])
