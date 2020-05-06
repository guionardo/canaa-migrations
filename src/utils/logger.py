import io
import json
import logging
import os
import traceback

__default_logger = None

DEBUG_LEVEL = None


def get_span_trace():
    return (0, 0)


def get_logger() -> logging.Logger:
    """ Get default logger for application"""
    global __default_logger, DEBUG_LEVEL
    if __default_logger:
        return __default_logger

    datadog_enabled = setup_datadog()

    DEBUG_LEVEL, dbg_level_str = _get_log_level()

    if not datadog_enabled or os.getenv("LOG_DEBUGGING", None):
        format_class = DebugLogFormatter('', '%Y-%m-%d %H:%M:%S')
    else:
        format_class = LogFormatter('', '%Y-%m-%d %H:%M:%S')

    fs = logging.StreamHandler()
    fs.setFormatter(format_class)
    __default_logger = logging.getLogger('default')
    __default_logger.setLevel(DEBUG_LEVEL)
    __default_logger.addHandler(fs)

    return __default_logger


def setup_datadog():
    try:
        # Testing, deactivate tracer
        from ddtrace import patch_all, tracer, helpers
        if not os.getenv('TESTING', False):
            tracer.configure()
            apm_env = os.environ.get('DD_APM_ENV')

            if apm_env:
                tracer.set_tags({'env': apm_env})
            patch_all(logging=True, pymongo=True)
            __datadog_enabled = True
            global get_span_trace
            get_span_trace = helpers.get_correlation_ids
        else:
            tracer.configure(enabled=False)
            __datadog_enabled = False

    except Exception as exc:    # pragma: no cover
        print("DATADOG LOAD ERROR: "+str(exc))
        __datadog_enabled = False

    return __datadog_enabled


def reset():
    '''
    Reset default logger
    '''
    if 'default' in logging.Logger.manager.loggerDict:
        del(logging.Logger.manager.loggerDict['default'])
    global __default_logger
    __default_logger = None


class LogFormatter(logging.Formatter):

    def formatException(self, ei):
        """
        Format an exception so that it prints on a single line.
        """
        with io.StringIO() as sio:
            traceback.print_exception(ei[0], ei[1], ei[2], None, sio)
            string_io_value = sio.getvalue()

        if string_io_value[-1:] == "\n":
            string_io_value = string_io_value[:-1]

        return repr(string_io_value)

    def format(self, record):
        """ Format logging message """

        trace_id, span_id = get_span_trace()

        formatted_message = {
            "date": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "file": f"{record.filename}:{record.lineno}",
            "dd.span_id": span_id,
            "dd.trace_id": trace_id
        }

        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)

        if record.exc_text:
            formatted_message["exception"] = record.exc_text

        return json.dumps(formatted_message, ensure_ascii=True)


class DebugLogFormatter(logging.Formatter):

    def formatException(self, ei):
        """
        Format an exception so that it prints on a single line.
        """
        with io.StringIO() as sio:
            traceback.print_exception(ei[0], ei[1], ei[2], None, sio)
            string_io_value = sio.getvalue()

        return string_io_value

    def format(self, record):
        """ Format logging message """

        ""
        formatted_message = \
            "{date} {level:8s}:{file:18s}({lineno:3d}) - {message}".format(
                date=self.formatTime(record, self.datefmt),
                level=record.levelname,
                file=record.filename,
                lineno=record.lineno,
                message=record.getMessage()
            )

        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)

        if record.exc_text:
            exc_text = "\n\t" + "\n\t".join(record.exc_text.split('\n'))
        else:
            exc_text = ""

        return formatted_message + exc_text


def _get_log_level():
    level = os.getenv('DEBUG_LEVEL', 'info').lower()

    if level in ['critical', '50']:
        return logging.CRITICAL, 'CRITICAL'
    elif level in ['error', '40']:
        return logging.ERROR, 'ERROR'
    elif level in ['warning', '30']:
        return logging.WARNING, 'WARNING'
    # elif level in ['info', '20']:
    #     return logging.INFO, 'INFO'
    elif level in ['debug', '10']:
        return logging.DEBUG, 'DEBUG'
    elif level in ['notset', '0', '00']:
        return logging.NOTSET, 'NOTSET'
    else:
        return logging.INFO, 'INFO'
