import logging
import typing as t

import structlog
from decouple import config

if config("PYTHON_RICH_STACKTRACE", default=False, cast=bool):
    from rich.traceback import install

    # not really logging, but this is a good place to set this up
    install(show_locals=True)


def configureLogger():
    logger_factory = structlog.PrintLoggerFactory()

    # allow user to specify a log in case they want to do something meaningful with the stdout
    if python_log_path := config("PYTHON_LOG_PATH", default=None):
        python_log = open(python_log_path, "a")
        logger_factory = structlog.PrintLoggerFactory(file=python_log)

    log_level = t.cast(str, config("LOG_LEVEL", default="WARN", cast=str))
    level = getattr(logging, log_level.upper())

    # TODO add thread logging and customized format
    # https://cs.github.com/GeoscienceAustralia/digitalearthau/blob/4cf486eb2a93d7de23f86ce6de0c3af549fe42a9/digitalearthau/uiutil.py#L45
    structlog.configure(
        # context_class enables thread-local logging to avoid passing a log instance around
        # https://www.structlog.org/en/21.1.0/thread-local.html
        # context_class=wrap_dict(dict),
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=logger_factory,
        cache_logger_on_first_use=True,
    )


configureLogger()

if t.cast(str, config("PYTHON_ENV", default="development", cast=str)).lower() == "production":
    import sentry_sdk

    sentry_sdk.init(
        dsn=t.cast(str, config("SENTRY_DSN", cast=str, required=True)),
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=1.0,
    )

log = structlog.get_logger()
