import unittest
from src.canaa_migrations import CanaaMigrations
from src.migration_setup import MigrationSetup


class TestCanaaMigrations(unittest.TestCase):

    def setUp(self):
        self.setup = MigrationSetup(
            'mongodb://localhost:27017/test_db')

    def test_generate(self):
        cm = CanaaMigrations(self.setup)
        filename = cm.generate()
        self.assertIsNotNone(filename)

    def test_upgrade(self):
        cm = CanaaMigrations(self.setup)
        cm.upgrade()
        
    def test_downgrade(self):
        cm = CanaaMigrations(self.setup)
        cm.downgrade()