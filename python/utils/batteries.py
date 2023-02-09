from contextlib import contextmanager
from time import perf_counter
from typing import Any, Iterable, List, TypeAlias, TypeVar, Union

# Collection of small helper functions that should be included in any language.. (Cough)


def unique(values):
    new_values = []
    for value in values:
        if value not in new_values:
            new_values.append(value)

    return new_values


# https://stackoverflow.com/questions/66030444/dealing-with-lack-of-non-null-assertion-operator-in-python
import typing as t

T = TypeVar("T")


def not_none(obj: t.Optional[T]) -> T:
    assert obj is not None
    return obj


from contextlib import ContextDecorator
from time import perf_counter

L = TypeVar("L")


# NOTE: python appears to not yet support recursive types
# NestedList: TypeAlias = List["NestedList[L] | L"]


# def flatten(lst: NestedList[L]) -> List[L]:
def flatten(lst: List[Any]) -> List:
    flattened_list = []
    for i in lst:
        if isinstance(i, list):
            flattened_list.extend(flatten(i))
        else:
            flattened_list.append(i)
    return flattened_list


# TODO there's got to be a package to do this for us, we can just hot-swap it out later
# https://stackoverflow.com/questions/33987060/python-context-manager-that-measures-time
class log_execution_time(ContextDecorator):
    def __init__(self, msg):
        self.msg = msg

    def __enter__(self):
        self.time = perf_counter()
        return self

    def __exit__(self, type, value, traceback):
        elapsed = perf_counter() - self.time
        print(f"{self.msg} took {elapsed:.3f} seconds")
