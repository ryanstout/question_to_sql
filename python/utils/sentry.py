import typing as t

import sentry_sdk
from decouple import config
from sentry_sdk.integrations.flask import FlaskIntegration

from python.utils.environments import is_production


def configure_sentry():
    if not is_production():
        return

    sentry_sdk.init(
        dsn=t.cast(str, config("SENTRY_DSN", cast=str)),
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=1.0,
        integrations=[
            FlaskIntegration(),
        ],
    )
