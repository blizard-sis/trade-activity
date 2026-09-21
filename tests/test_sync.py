import unittest
from unittest.mock import patch

import test_journal
from backend.storage import database


class SyncTests(unittest.TestCase):
    setUp = test_journal.JournalTests.setUp

    def test_counts_new_changed_and_repeated_trades(self):
        trades = database.get_trades({})
        self.assertEqual(database.save_trades(trades, with_counts=True), dict(added=0, updated=0, unchanged=2))
        trades[0]['price'] += 1
        trades.append({**trades[1], 'trade_id': 'new'})
        self.assertEqual(database.save_trades(trades, with_counts=True), dict(added=1, updated=1, unchanged=1))
        self.assertEqual(database.save_trades(trades + trades, with_counts=True), dict(added=0, updated=0, unchanged=3))
        self.assertEqual(database.save_trades([], with_counts=True), dict(added=0, updated=0, unchanged=0))

    def test_sync_response_aggregates_accounts(self):
        self.app.config['TBANK_TOKEN'] = 'test'
        with patch('backend.services.sync.TBankClient') as client:
            client.return_value.accounts.return_value = [{'id': 'a'}, {'id': 'b'}]
            client.return_value.operations.return_value = []
            response = self.client.post('/api/sync')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), dict(accounts=2, added=0, updated=0, unchanged=0, saved=0))
