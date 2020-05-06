import datetime

import pymongo

from src.migration_action import MigrationAction
from src.migration_exception import MigrationException
from src.migration_setup import MigrationSetup


class MigrationStateData:

    def __init__(self, from_data=None):
        self.name: str = None
        self.applied: datetime.datetime = None
        self.description: str = None
        self.running_time: int = 0
        if isinstance(from_data, dict):
            self.name = from_data.get('_id', None)
            self.applied = from_data.get('applied', None)
            self.description = from_data.get('description', None)
            self.running_time = from_data.get('running_time', 0)

    def to_dict(self):
        return {"_id": self.name,
                "applied": self.applied,
                "description": self.description,
                "running_time": self.running_time}

    def __str__(self):
        return "{0:20} - {1:20} - {2}".format(
            self.name,
            'NOT APPLIED' if not self.applied else str(self.applied),
            self.description
        )


class MigrationState:

    def __init__(self, setup: MigrationSetup):
        if not setup.is_ok:
            raise MigrationException("Invalid setup for migration state")
        self.__setup = setup

    def read_states(self, names: list) -> list:
        m_states = self.__setup.collection.find({"_id": {'$in': names}})

        states = []
        for state in m_states:
            msd = MigrationStateData(state)
            states.append(msd)
        return states

    def read_state(self, migration_name: str) -> MigrationStateData:
        data = self.__setup.collection.find_one({"_id": migration_name})
        if data:
            return MigrationStateData(data)
        return MigrationStateData({"_id": migration_name})

    def write_state(self, msd: MigrationStateData):
        self.__setup.collection.replace_one(
            {"_id": msd.name},
            msd.to_dict(),
            upsert=True
        )
