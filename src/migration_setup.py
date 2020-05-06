import glob
import os
import datetime
from typing import List
import pymongo
from bson import CodecOptions

from src.migration_action import MigrationAction
from src.migration_exception import MigrationException
from src.utils.command_logger import CommandLogger
from src.utils.logger import get_logger


class MigrationSetup:

    LOG = get_logger()

    def __init__(self, mongodb_uri,
                 migrations_package='migrations',
                 migrations_collection='canaa_migrations'):
        """
        :param mongodb_uri: str 'mongodb://user:password@host:27017/database'
        :param migrations_package: str 'migrations'
        :param migrations_collection: str 'canaa_migrations'
        """
        self.__mongodb_uri = mongodb_uri
        self.__migrations_package = migrations_package
        self.__migrations_collection = migrations_collection
        self.__migrations = []
        self.__client = None
        self.__collection = None
        self.__ok = self._validate()

    @property
    def is_ok(self) -> bool:
        return self.__ok

    @property
    def db(self) -> pymongo.MongoClient:
        if self.__ok:
            return self.__client.get_database()

    @property
    def collection(self) -> pymongo.collection.Collection:
        if self.__ok:
            if not self.__collection:
                self.__collection = self.db[self.__migrations_collection].with_options(
                    codec_options=CodecOptions(
                        tz_aware=True, tzinfo=datetime.timezone.utc)
                )

            return self.__collection

        return None

    @property
    def migrations_folder(self):
        folder = os.path.sep.join(self.__migrations_package.split('.'))
        return os.path.abspath(folder)

    @property
    def migrations(self) -> List[MigrationAction]:
        return self.__migrations

    def _validate(self):
        try:
            self.__client = pymongo.MongoClient(
                self.__mongodb_uri,
                event_listeners=[CommandLogger()])
        except Exception as exc:
            self.LOG.error('EXCEPTION ON CONNECT TO MONGO: %s', str(exc))
            return False

        migrations_folder = self.migrations_folder
        if not os.path.isdir(migrations_folder):
            self.LOG.error(
                'MIGRATION PACKAGE FOLDER NOT FOUND %s', migrations_folder)
            return False

        migrations_files = glob.glob(os.path.join(migrations_folder, '*.py'))

        return self._validate_migrations(migrations_files)

    def _validate_migrations(self, migrations_files):
        migrations = []
        for migration_file in migrations_files:
            module_file = self.__migrations_package + \
                '.'+os.path.basename(migration_file)[:-3]
            try:
                migration = MigrationAction(module_file)
                migrations.append(migration)
            except Exception as exc:
                self.LOG.error('MIGRATION MODULE %s WITH ERROR %s',
                               module_file, str(exc))
                return False

        if len(migrations) == 0:
            self.LOG.warning('NO MIGRATIONS FOUND IN PACKAGE %s',
                             self.__migrations_package)
        self.__migrations = migrations
        return True
