import os

import dotenv

from src.migration_exception import MigrationException
from src.migration_setup import MigrationSetup
from src.utils.logger import get_logger

LOG = get_logger()


def setup_from_env() -> MigrationSetup:
    dotenv.load_dotenv()
    # MongoURI = user:pass@host:port/db
    mongodb_uri = os.getenv('MONGODB_URI', None)
    mongodb_database = os.getenv('MONGODB_DATABASE', None)

    if not (mongodb_uri and mongodb_database):
        raise MigrationException(
            'MONGODB_URI / MONGODB_DATABASE INVALID OR MISSING')
    mongodb_uri = mongodb_uri+'/'+mongodb_database

    migrations_package = os.getenv('MIGRATIONS_PACKAGE', 'migrations')
    migrations_collection = os.getenv(
        'MIGRATIONS_COLLECTION', 'canaa_migrations')
    return MigrationSetup(mongodb_uri, migrations_package, migrations_collection)


def setup_from_args(args, ignore_mongodb: bool = False) -> MigrationSetup:
    mig_coll = getattr(args, 'migrations_collection', None)
    if not mig_coll:
        raise MigrationException('Migrations collection is missing')
    mig_pack = getattr(args, 'migrations_package', None)
    if not mig_pack:
        raise MigrationException('Migrations package is missing')

    uri_mongo = getattr(args, 'uri_mongodb', None)
    if not uri_mongo:
        dotenv.load_dotenv()
        mongodb_uri = os.getenv('MONGODB_URI', None)
        mongodb_database = os.getenv('MONGODB_DATABASE', None)

        if not (mongodb_uri and mongodb_database):
            if ignore_mongodb:
                mongodb_uri = 'mongodb://localhost:27017'
                mongodb_database = 'test'
            else:
                raise MigrationException(
                    'MONGODB_URI / MONGODB_DATABASE INVALID OR MISSING')
        uri_mongo = mongodb_uri+'/'+mongodb_database
        # LOG.warning('MongoDB URI read from environment: %s', uri_mongo)

    return MigrationSetup(uri_mongo, mig_pack, mig_coll)
