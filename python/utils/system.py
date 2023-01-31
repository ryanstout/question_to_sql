import typing as t

from decouple import config


def is_production():
    return t.cast(str, config("PYTHON_ENV", default="development", cast=str)).lower() == "production"
