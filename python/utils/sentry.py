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
        traces_sample_rate=0.1,
        integrations=[
            FlaskIntegration(),
        ],
    )
