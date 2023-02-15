# isort:skip_file
import logging
import typing as t

import structlog
from decouple import config

from python.utils.sentry import configure_sentry

# we be monkey patching
import colorama
import pretty_traceback
from pretty_traceback.formatting import (
    FMT_CALL,
    FMT_CONTEXT,
    FMT_LINENO,
    FMT_MODULE,
    PaddedRow,
)

# TODO could submit a PR using named format string pieces
# https://github.com/mbarkhau/pretty-traceback/blob/b5e06b2022a806127b1b7b5ba7972afb84e48e08/src/pretty_traceback/formatting.py#L287
def _patched_rows_to_lines(rows: t.List[PaddedRow], color: bool = False) -> t.Iterable[str]:

    # apply colors and additional separators/ spacing
    fmt_module = FMT_MODULE if color else "{0}"
    fmt_call = FMT_CALL if color else "{0}"
    fmt_lineno = FMT_LINENO if color else "{0}"
    fmt_context = FMT_CONTEXT if color else "{0}"

    for alias, short_module, full_module, call, lineno, context in rows:
        if short_module:
            _alias = alias
            module = short_module
        else:
            _alias = ""
            module = full_module

        # NOTE main goal is getting line number with file so VS code can open it
        parts = (
            " ",
            _alias,
            " ",
            fmt_module.format(module.strip()) + ":" + fmt_lineno.format(lineno.strip()),
            "  ",
            fmt_call.format(call),
            fmt_context.format(context),
        )

        # original is pretty_traceback.formatting._padded_rows
        # TODO need to add left passing to the trace, but this is workable for now

        line = "".join(parts)

        if alias == "<pwd>":
            yield line.replace(colorama.Style.NORMAL, colorama.Style.BRIGHT)
        else:
            yield line


pretty_traceback.formatting._rows_to_lines = _patched_rows_to_lines
pretty_traceback.install()


def configure_logger():
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


configure_logger()
configure_sentry()

log = structlog.get_logger()
