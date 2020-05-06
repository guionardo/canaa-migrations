import unittest
from src.migration_setup import  MigrationSetup

class TestMigrationSetup(unittest.TestCase):

    def test_init(self):
        ms = MigrationSetup('mongodb://localhost:27017/test_db')
        self.assertTrue(ms.is_ok)
        coll = ms.collection
        self.assertIsNotNone(coll)
