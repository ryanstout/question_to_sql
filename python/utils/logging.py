import logging
import os

import structlog
from decouple import config

if not os.getenv("SKIP_RICH"):
    from rich.traceback import install

    # not really logging, but this is a good place to set this up
    install(show_locals=True)


def setLevel(level):
    level = getattr(logging, level.upper())

    python_log_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../", "python.log"))
    python_log = open(python_log_path, "a")

    # TODO add thread logging and customized format
    # https://cs.github.com/GeoscienceAustralia/digitalearthau/blob/4cf486eb2a93d7de23f86ce6de0c3af549fe42a9/digitalearthau/uiutil.py#L45
    structlog.configure(
        # context_class enables thread-local logging to avoid passing a log instance around
        # https://www.structlog.org/en/21.1.0/thread-local.html
        # context_class=wrap_dict(dict),
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(file=python_log),
        cache_logger_on_first_use=True,
    )


log_level = config("LOG_LEVEL", default="WARN")
setLevel(log_level)

log = structlog.get_logger()
