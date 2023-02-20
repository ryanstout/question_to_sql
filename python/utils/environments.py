import typing as t

from decouple import config


def _python_env():
    return t.cast(str, config("PYTHON_ENV", default="development", cast=str)).lower()


def is_testing():
    return _python_env() == "test"


def is_production():
    return _python_env() == "production"


def is_development():
    return _python_env() == "development"
