import argparse
import os

from src.canaa_migrations import CanaaMigrations
from src.cli.cli_downgrade import cli_downgrade
from src.cli.cli_generate import cli_generate
from src.cli.cli_list import cli_list
from src.cli.cli_upgrade import cli_upgrade
from src.migration_setup import MigrationSetup
from src.utils.command_logger import CommandLogger


def main():
    parser = setup_parser()

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


def setup_parser():
    parser = argparse.ArgumentParser(
        prog='canaa-migrate',
        description='Migration tool for canaa')

    parser.add_argument('-u', '--uri-mongodb',
                        help='URI MongoDB [user]:[password]@host:port/database')
    parser.add_argument('-m', '--migrations-package',
                        default='migrations',
                        help='Migrations package')
    parser.add_argument('-c', '--migrations-collection',
                        default='canaa_migrations',
                        help='Collection to store migrations')

    subparsers = parser.add_subparsers()

    list_migrations = subparsers.add_parser(
        'list', help="Show migrations list")

    list_migrations.add_argument('--show-state', action='store_true',
                                 default=False, help="Show state of migration on database")
    list_migrations.set_defaults(func=cli_list)

    generate = subparsers.add_parser('generate',
                                     help='Generates a new migration file')
    generate.set_defaults(func=cli_generate)

    upgrade = subparsers.add_parser('upgrade',
                                    help='Upgrades database')
    upgrade.add_argument('--until',
                         help="Run upgrade until named migration",
                         action='store')
    upgrade.set_defaults(func=cli_upgrade)

    downgrade = subparsers.add_parser('downgrade', help='Downgrades database')
    downgrade.add_argument('--keep',
                           help="Run downgrade until named migration",
                           action='store')
    downgrade.set_defaults(func=cli_downgrade)

    return parser


if __name__ == "__main__":
    os.environ.update({'LOG_DEBUGGING': 'True'})
    CommandLogger.ENABLED = False
    main()
