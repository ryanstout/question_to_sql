import typing as t

import sentry_sdk
from decouple import config
from sentry_sdk.integrations.flask import FlaskIntegration

from python.utils.environments import is_production


def configure_sentry():
    if not is_production():
        return

    # TODO no docs for this, post somewhere + document
    def filter_transactions(event, _hint):
        from urllib.parse import urlparse  # pylint: disable=import-outside-toplevel

        url_string = event["request"]["url"]
        parsed_url = urlparse(url_string)

        if parsed_url.path == "/healthcheck":
            return None

        return event

    sentry_sdk.init(
        dsn=t.cast(str, config("SENTRY_DSN", cast=str)),
        traces_sample_rate=0.1,
        integrations=[
            FlaskIntegration(),
        ],
        before_send_transaction=filter_transactions,
    )
