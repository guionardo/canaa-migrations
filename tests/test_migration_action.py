import unittest
from src.migration_action import MigrationAction


class TestMigrationAction(unittest.TestCase):

    def test_valid_migration(self):
        ma = MigrationAction('tests.migrations.migration_ok')
        self.assertTrue(ma.is_ok)

    def test_invalid_migration_invalid_methods(self):
        with self.assertRaises(Exception):
            MigrationAction('tests.migrations.migration_invalid_methods')
