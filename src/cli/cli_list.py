from src.canaa_migrations import CanaaMigrations
from src.cli.read_setup import setup_from_args
from src.migration_setup import MigrationSetup
from src.migration_state import MigrationState, MigrationStateData


def cli_list(args):

    try:
        setup = setup_from_args(args, not args.show_state)
    except Exception as exc:
        print('Error on setup: '+str(exc))
        return

    migrations = CanaaMigrations(setup)
    states = MigrationState(setup)

    if args.show_state:
        print('MIGRATIONS in {0} -> {1}:{2}/{3}'.format(setup.migrations_folder,
                                                        setup.db.client.HOST,
                                                        setup.db.client.PORT,
                                                        setup.db.name))

        table = Table('Name', 'Date/Time', 'Description')
    else:
        print('MIGRATIONS IN {0}'.format(setup.migrations_folder))
        table = Table('Name', 'Description')

    migration_names = [
        migration.name for migration in migrations._setup.migrations]
    state_list = states.read_states(migration_names)
    for migration in migrations._setup.migrations:
        if args.show_state:
            state = None
            for stt in state_list:
                if stt.name == migration.name:
                    state = stt
                    break
            if not state:
                state = MigrationStateData(
                    {'_id': migration.name, 'description': migration.description})
            table.add(state.name, state.applied, state.description)

        else:
            state = MigrationStateData(
                {'_id': migration.name, 'description': migration.description})
            table.add(migration.name, migration.description)

    table.print()


class Table:

    def __init__(self, *heads):
        self.heads = heads
        self.max = [len(heads[i]) for i in range(len(heads))]
        self.lines = []

    def add(self, *data):
        if len(data) != len(self.max):
            return
        line = []
        for i, k in enumerate(data):
            k = str(k)
            self.max[i] = max(self.max[i], len(k))
            line.append(k)

        self.lines.append(line)

    def print(self):
        print(' '.join([self.heads[i].ljust(self.max[i])
                        for i in range(len(self.max))]))

        print(' '.join(['='*i for i in self.max]))
        for line in self.lines:
            print(' '.join([line[i].ljust(self.max[i])
                            for i in range(len(self.max))]))
        print(' '.join(['='*i for i in self.max]))
