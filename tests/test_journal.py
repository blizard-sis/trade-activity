import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend import create_app
from backend.storage import database


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        path = Path(self.temp.name) / 'journal.sqlite3'
        self.db_patch = patch.object(database, 'DATABASE', path)
        self.db_patch.start()
        self.addCleanup(self.db_patch.stop)
        # Start from the old schema to exercise the real upgrade path.
        with sqlite3.connect(path) as db:
            db.execute("CREATE TABLE position_notes (position_id TEXT PRIMARY KEY, entry_note TEXT NOT NULL DEFAULT '', exit_note TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
            db.execute("INSERT INTO position_notes (position_id, entry_note, exit_note) VALUES ('a:instrument:buy:long', 'Старый план', 'Старый выход')")
        with patch('backend.load_config', return_value={}):
            self.app = create_app()
        self.client = self.app.test_client()
        database.save_account({'id': 'a', 'name': 'Test account'})
        trades = []
        for trade_id, side, price, date in [('buy', 'buy', 100, '2026-09-01T10:00:00Z'), ('sell', 'sell', 110, '2026-09-02T10:00:00Z')]:
            trade = dict.fromkeys(database.TRADE_FIELDS, '')
            trade.update(account_id='a', trade_id=trade_id, operation_id=trade_id, instrument_uid='instrument', ticker='TEST', instrument_name='Test', side=side, quantity=1, price=price, currency='rub', commission=1, commission_currency='rub', payment=-price if side == 'buy' else price, payment_currency='rub', executed_at=date)
            trades.append(trade)
        database.save_trades(trades)
        self.position_id = 'a:instrument:buy:long'

    def test_migration_preserves_notes_and_is_repeatable(self):
        database.initialize()
        item = self.client.get('/api/journal').get_json()[0]
        self.assertEqual(item['entry_note'], 'Старый план')
        self.assertEqual(item['exit_note'], 'Старый выход')
        self.assertNotIn('lessons', item)
        self.assertNotIn('emotions', item)
        self.assertEqual(item['exit_assessment']['reason'], 'manual')

    def test_save_survives_reinitialization_without_changing_facts(self):
        before = database.get_trades({})
        values = dict.fromkeys(database.JOURNAL_FIELDS, '')
        values.update(entry_note='План', planned_stop='95,5', planned_take='120')
        response = self.client.put('/api/journal/' + self.position_id, json=values)
        self.assertEqual(response.status_code, 200)
        database.initialize()
        loaded = self.client.get('/api/journal').get_json()[0]
        for key, value in values.items():
            self.assertEqual(loaded[key], value)
        self.assertEqual(database.get_trades({}), before)
        self.assertEqual(loaded['exit_assessment']['reason'], 'manual')
        exported = self.client.get('/api/positions/export').get_json()['positions'][0]
        self.assertTrue(exported['exit_assessment']['inferred'])
        self.assertEqual(exported['planned_take'], '120')
        self.assertEqual(self.client.get('/api/monthly').status_code, 200)
        self.assertEqual(self.client.get('/api/positions/export').status_code, 200)

    def test_validation_and_unknown_position(self):
        for body in ([], {'planned_stop': 7}, {'exit_note': []}, {'entry_note': 'a' * 20001}):
            self.assertEqual(self.client.put('/api/journal/' + self.position_id, json=body).status_code, 400)
        self.assertEqual(self.client.put('/api/journal/missing', json={}).status_code, 404)
        self.assertEqual(self.client.get('/api/journal').get_json()[0]['entry_note'], 'Старый план')

    def test_legacy_note_update_keeps_new_fields(self):
        values = dict.fromkeys(database.JOURNAL_FIELDS, '')
        values['planned_stop'] = '95'
        self.client.put('/api/journal/' + self.position_id, json=values)
        self.client.put('/api/positions/' + self.position_id + '/notes', json={'entry_note': 'Новый вход', 'exit_note': ''})
        item = self.client.get('/api/journal').get_json()[0]
        self.assertEqual(item['entry_note'], 'Новый вход')
        self.assertEqual(item['planned_stop'], '95')


    def test_hidden_notes_survive_save(self):
        with database.connect() as db:
            db.execute("ALTER TABLE position_notes ADD COLUMN emotions TEXT NOT NULL DEFAULT ''")
            db.execute("ALTER TABLE position_notes ADD COLUMN lessons TEXT NOT NULL DEFAULT ''")
            db.execute("UPDATE position_notes SET emotions = 'Старые эмоции', lessons = 'Старый вывод'")
        database.initialize()
        values = dict.fromkeys(database.JOURNAL_FIELDS, '')
        values['exit_note'] = 'Комментарий'
        self.assertEqual(self.client.put('/api/journal/' + self.position_id, json=values).status_code, 200)
        with database.connect() as db:
            row = db.execute("SELECT emotions, lessons FROM position_notes WHERE position_id = ?", (self.position_id,)).fetchone()
        self.assertEqual(tuple(row), ('Старые эмоции', 'Старый вывод'))


if __name__ == '__main__':
    unittest.main()
