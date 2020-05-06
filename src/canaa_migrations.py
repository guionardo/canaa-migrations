import datetime
import importlib
import os
import time

from src.migration_action import MigrationAction
from src.migration_setup import MigrationSetup
from src.migration_state import MigrationState
from src.utils.logger import get_logger


class CanaaMigrations:

    LOG = get_logger()

    def __init__(self, setup: MigrationSetup):
        self._setup: MigrationSetup = setup
        self._states = MigrationState(self._setup)

    def generate(self) -> str:
        """ Generates a migration file and returns file name """
        if not os.path.isdir(self._setup.migrations_folder):
            try:
                os.makedirs(self._setup.migrations_folder)
                self.LOG.info('Created migrations folder in %s',
                              self._setup.migrations_folder)
            except Exception as exc:
                self.LOG.error(
                    'EXCEPTION on creating migrations folder: %s', str(exc))
                return None

        dc = datetime.datetime.utcnow()
        filename = os.path.join(
            self._setup.migrations_folder,
            dc.strftime('%Y%m%d_%H%M%S_migration.py'))

        try:
            default_migration_module = importlib.import_module(
                'src.default_migration')

            with open(default_migration_module.__file__) as f:
                default_migration = f.read()

            with open(filename, 'w') as f:
                f.write(default_migration.replace('{{DATETIME}}', str(dc)))

            self.LOG.info('Created migration file in %s', filename)
            return filename
        except Exception as exc:
            self.LOG.error(
                'EXCEPTION on creating migration file: %s', str(exc))

    def upgrade(self, until_name: str = None):
        """
        Executes upgrade until migration named until_name (inclusive).
        If not informed, upgrades all migrations
        """
        self.LOG.info('Starting upgrade')
        t0 = time.time()
        just_applied = []
        successful_migrations = []
        unsuccessful_migrations = []
        for migration in self._setup.migrations:
            state = self._states.read_state(migration.name)
            if state.applied:
                just_applied.append(migration.name)
                continue
            t1 = time.time()
            migration_success, can_continue = self.apply_upgrade(migration)

            if migration_success:
                state.applied = datetime.datetime.now()
                state.description = migration.description
                state.running_time = int((time.time()-t1) * 1000)
                self._states.write_state(state)
                successful_migrations.append(migration.name)
            else:
                unsuccessful_migrations.append(migration.name)

            if not can_continue:
                self.LOG.warning(
                    'Stopped next migrations by after_upgrade method result')
                break
            if migration.name == until_name:
                self.LOG.info('Stopped migrations until %s', until_name)
                break
        if just_applied:
            self.LOG.info('PREVIOUSLY APPLIED: %s', just_applied)
        if unsuccessful_migrations:
            self.LOG.info('UNSUCCESSFUL MIGRATIONS: %s',
                          unsuccessful_migrations)
        if successful_migrations:
            self.LOG.info('SUCCESSFUL MIGRATIONS: %s', successful_migrations)
        self.LOG.info('Ending upgrade: %s ms', int((time.time()-t0)*1000))

    def downgrade(self, keep_name: str = None):
        """
        Executes downgrade until migration named keep_name (exclusive)
        If not informed, downgrade all migrations
        """
        self.LOG.info('Starting downgrade')
        t0 = time.time()
        dont_applied = []
        successful_downgrades = []
        unsuccessful_downgrades = []
        self._setup.migrations.reverse()
        for migration in self._setup.migrations:
            if migration.name == keep_name:
                self.LOG.info('Stopped downgrade proccess to %s', keep_name)
                break
            state = self._states.read_state(migration.name)
            if not state.applied:
                dont_applied.append(migration.name)
                continue
            t1 = time.time()
            migration_success, can_continue = self.apply_downgrade(migration)

            if migration_success:
                state.applied = None
                state.description = state.description + \
                    ' [UNDONE IN {0}]'.format(datetime.datetime.now())
                state.running_time = int((time.time()-t1)*1000)
                self._states.write_state(state)
                successful_downgrades.append(migration.name)
            else:
                unsuccessful_downgrades.append(migration.name)

            if not can_continue:
                self.LOG.warning(
                    'Stopped downgrade by after_downgrade method result')
                break

        self._setup.migrations.reverse()
        if dont_applied:
            self.LOG.info('DON´T APPLIED MIGRATIONS: %s', dont_applied)
        if unsuccessful_downgrades:
            self.LOG.info('UNSUCCESSFUL DOWNGRADES: %s',
                          unsuccessful_downgrades)
        if successful_downgrades:
            self.LOG.info('SUCCESSFUL DOWNGRADES: %s', successful_downgrades)
        self.LOG.info('Ending downgrade: %s ms', int((time.time()-t0)*1000))

    def apply_upgrade(self, migration: MigrationAction) -> bool:
        if not self.can_upgrade(migration):
            self.LOG.warning('MIGRATION INTERRUPTED')
            return False, False
        self.LOG.info('Applying upgrade %s: %s',
                      migration.name, migration.description)
        migration_success = False
        migration_exception = None
        can_continue = False
        can_continue_exception = None
        try:
            migration_success = migration.upgrade(self._setup.db)
        except Exception as exc:
            migration_exception = exc

        if migration_success:
            self.LOG.info('Successful aplyied upgrade %s', migration.name)
            try:
                can_continue = migration.after_upgrade(None)
            except Exception as exc:
                can_continue_exception = exc
        else:
            self.LOG.error('Failed to apply upgrade %s: %s',
                           migration.name, str(migration_exception))
            try:
                can_continue = migration.after_upgrade(migration_exception)
            except Exception as exc:
                can_continue_exception = exc

        if not can_continue:
            if can_continue_exception:
                self.LOG.error(
                    'MIGRATION INTERRUPTED BY EXCEPTION %s', can_continue_exception)
            else:
                self.LOG.warning(
                    'MIGRATION INTERRUPTED BY after_upgrade EVENT')

        return migration_success, can_continue

    def can_upgrade(self, migration: MigrationAction) -> bool:
        """ Can upgrade only if all dependency migrations are applied """
        if not migration.dependencies:
            return True
        states = self._states.read_states(migration.dependencies)
        missing = []
        for dependency in migration.dependencies:
            found = False
            for state in states:
                if state.name == dependency and state.applied:
                    found = True
                    break
            if not found:
                missing.append(dependency)

        if missing:
            self.LOG.warning(
                'MISSING DEPENDENCY MIGRATIONS FOR %s: %s', migration.name, missing)
        return not missing

    def apply_downgrade(self, migration: MigrationAction) -> bool:
        if not self.can_downgrade(migration):
            self.LOG.warning('DOWNGRADE INTERRUPTED')
            return False, False
        self.LOG.info('Undoing migration %s: %s',
                      migration.name, migration.description)
        migration_success = False
        migration_exception = None
        can_continue = False
        can_continue_exception = None
        try:
            migration_success = migration.downgrade(self._setup.db)
        except Exception as exc:
            migration_exception = exc

        if migration_success:
            self.LOG.info('Successful downgraded %s', migration.name)
            try:
                can_continue = migration.after_downgrade(None)
            except Exception as exc:
                can_continue_exception = exc
        else:
            self.LOG.error('Failed to downgrade %s: %s',
                           migration.name, str(migration_exception))
            try:
                can_continue = migration.after_downgrade(migration_exception)
            except Exception as exc:
                can_continue_exception = exc

        if not can_continue:
            if can_continue_exception:
                self.LOG.error(
                    'DOWNGRADE INTERRUPTED BY EXCEPTION %s', can_continue_exception)
            else:
                self.LOG.warning(
                    'DOWNGRADE INTERRUPTED BY after_downgrade EVENT')

        return migration_success, can_continue

    def can_downgrade(self, migration: MigrationAction) -> bool:
        """ Can downgrade only all depending migrations are not applied """
        all_dependents = set()
        dependents_names = self.find_dependents(migration.name, all_dependents)
        dependents = [
            dep for dep in self._setup.migrations if dep.name in dependents_names]

        if not dependents:
            return True
        pending_downgrades = []
        states = self._states.read_states(
            [dependent.name for dependent in dependents])
        for dependent in dependents:
            found = False
            for state in states:
                if state.name == dependent.name and state.applied:
                    found = True
                    break
            if found:
                pending_downgrades.append(dependent.name)
        if pending_downgrades:
            self.LOG.warning('PENDING DOWNGRADE MIGRATIONS FOR %s: %s',
                             migration.name, pending_downgrades)

        return not pending_downgrades

    def find_dependents(self, migration_name: str, all_dependents: set) -> list:
        dependents = [mig
                      for mig in self._setup.migrations
                      if migration_name in mig.dependencies]

        for dependent in dependents:
            if dependent.name not in all_dependents:
                all_dependents.add(dependent.name)
                self.find_dependents(dependent.name, all_dependents)

        return list(all_dependents)

    # def get_migrations(self):
    #     for migration in self._setup.migrations:
