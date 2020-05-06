import pymongo

from .logger import get_logger


class CommandLogger(pymongo.monitoring.CommandListener):
    ENABLED = True

    def __init__(self):
        self.log = get_logger()

    def started(self, event):
        if self.ENABLED:
            self.log.info('STARTED: %s#%s : %s', event.command_name,
                          event.request_id, event.command)

    def succeeded(self, event):
        if self.ENABLED:
            self.log.info('SUCCEDED: %s#%s : %sus', event.command_name,
                          event.request_id, event.duration_micros)

    def failed(self, event):
        if self.ENABLED:
            self.log.error('FAILED: %s%%s : %sus', event.command_name,
                           event.request_id, event.duration_micros)
