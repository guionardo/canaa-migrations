import importlib
import inspect

from src.migration_exception import MigrationException


class MigrationAction:

    __slots__ = ['__ok', '__description', '__name',
                 '__upgrade', '__downgrade', '__dependencies',
                 '__after_upgrade', '__after_downgrade']

    def __init__(self, module_file):
        self.__ok = False
        module = importlib.import_module(module_file)

        self.__description = module.__doc__
        self.__name = module.__name__.split('.')[-1]
        self.__upgrade = self._validate_method(module, 'upgrade')
        self.__downgrade = self._validate_method(module, 'downgrade')
        self.__dependencies = self._validate_field(
            module, 'dependencies', must_exists=False) or []
        self.__after_upgrade = self._validate_method(
            module, 'after_upgrade', must_exist=False) or (lambda x: True)
        self.__after_downgrade = self._validate_method(
            module, 'after_downgrade', must_exist=False) or (lambda x: True)

        if isinstance(self.__dependencies, str):
            self.__dependencies = [self.__dependencies]
        if isinstance(self.__dependencies, list):
            self.__dependencies = [str(f) for f in self.__dependencies]
        else:
            raise MigrationException(
                'Migration module {0} must have and dependencies field with a string or list of strings value'.format(module.___name__))

        self.__ok = True

    @property
    def description(self) -> str:
        return self.__description

    @property
    def name(self) -> str:
        return self.__name

    @property
    def dependencies(self) -> list:
        return self.__dependencies

    @property
    def is_ok(self) -> bool:
        return self.__ok

    def _validate_method(self, module, method__name, argument_count=1, must_exist: bool = True):
        method = getattr(module, method__name, None)
        if callable(method) and len(inspect.signature(method).parameters) == argument_count:
            return method
        if not must_exist:
            return None

        raise MigrationException(
            'Migration module {0} must have an {1} method with {2} argument(s)'.format(module.__name__, method__name, argument_count))

    def _validate_field(self, module, field_name, must_exists=False):
        field = getattr(module, field_name, None)
        if field is None and must_exists:
            raise MigrationException('Migration module {0} must have a field {0}'.format(
                module.__name__, field_name))
        return field

    def upgrade(self, db):
        if self.__ok and self.__upgrade:
            return self.__upgrade(db)

    def downgrade(self, db):
        if self.__ok and self.__downgrade:
            return self.__downgrade(db)

    def after_upgrade(self, raised_exception: Exception):
        if self.__ok:
            return self.__after_upgrade(raised_exception)
        return True

    def after_downgrade(self, raised_exception: Exception):
        if self.__ok:
            return self.__after_downgrade(raised_exception)
        return True


def default_after_done(raised_exception) -> bool:
    return True
