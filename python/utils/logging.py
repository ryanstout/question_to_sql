import logging

import structlog
from decouple import config
from rich.traceback import install

# not really logging, but this is a good place to set this up
install(show_locals=True)


def setLevel(level):
    level = getattr(logging, level.upper())
    # TODO add thread logging and customized format
    structlog.configure(
        # context_class enables thread-local logging to avoid passing a log instance around
        # https://www.structlog.org/en/21.1.0/thread-local.html
        # context_class=wrap_dict(dict),
        # wrapper_class=structlog.make_filtering_bound_logger(level),
        cache_logger_on_first_use=True
    )


log_level = config("LOG_LEVEL", default="WARN")
setLevel(log_level)

log = structlog.get_logger()
