import typing as t

from decouple import config

from python.utils.system import is_production


def configure_sentry():
    if is_production():
        import sentry_sdk

        sentry_sdk.init(
            dsn=t.cast(str, config("SENTRY_DSN", cast=str)),
            # Set traces_sample_rate to 1.0 to capture 100%
            # of transactions for performance monitoring.
            # We recommend adjusting this value in production.
            traces_sample_rate=1.0,
        )
