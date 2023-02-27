import typing as t

import sentry_sdk
from decouple import config
from sentry_sdk.integrations.flask import FlaskIntegration

from python.utils.environments import is_production
from python.utils.logging import log


def configure_sentry():
    if not is_production():
        return

    log.info("configuring sentry")

    # TODO https://github.com/getsentry/sentry-docs/pull/6364/files
    def filter_transactions(event, _hint):
        from urllib.parse import urlparse  # pylint: disable=import-outside-toplevel

        url_string = event["request"]["url"]
        parsed_url = urlparse(url_string)

        if parsed_url.path == "/healthcheck":
            return None

        return event

    sentry_dsn = config("SENTRY_DSN", cast=str)
    assert sentry_dsn, "SENTRY_DSN is not set"

    sentry_sdk.init(
        dsn=t.cast(str, sentry_dsn),
        traces_sample_rate=0.1,
        integrations=[
            FlaskIntegration(),
        ],
        before_send_transaction=filter_transactions,
    )
