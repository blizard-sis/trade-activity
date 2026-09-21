import sqlite3
import unittest
from unittest.mock import patch

from backend.storage import database


class TransactionTests(unittest.TestCase):
    def test_connection_closes_after_commit(self):
        connection = sqlite3.connect(':memory:')
        with patch.object(database, 'connect', return_value=connection):
            with database.transaction() as db:
                db.execute('CREATE TABLE example (value INTEGER)')
        with self.assertRaises(sqlite3.ProgrammingError):
            connection.execute('SELECT 1')

    def test_connection_closes_after_failure(self):
        connection = sqlite3.connect(':memory:')
        with patch.object(database, 'connect', return_value=connection):
            with self.assertRaisesRegex(ValueError, 'failure'):
                with database.transaction():
                    raise ValueError('failure')
        with self.assertRaises(sqlite3.ProgrammingError):
            connection.execute('SELECT 1')

    def test_empty_import_does_not_open_database(self):
        with patch.object(database, 'connect') as connect:
            self.assertEqual(database.save_imported_positions([]), dict(added=0, updated=0, unchanged=0))
            connect.assert_not_called()
