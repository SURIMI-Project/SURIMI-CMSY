import logging


class _ConditionalLoggingLevelFormatter(logging.Formatter):
    def __init__(self):
        super().__init__(datefmt='%H:%M:%S')
        self._fmt_info  = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%H:%M:%S')
        self._fmt_level = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%H:%M:%S')

    def format(self, record):
        if record.levelno < logging.WARNING:
            return self._fmt_info.format(record)
        return self._fmt_level.format(record)
