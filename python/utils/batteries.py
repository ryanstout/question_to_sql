# Collection of small helper functions that should be included in any language.. (Cough)
from contextlib import ContextDecorator
from time import perf_counter
from typing import Optional, TypeAlias, TypeVar, Union

from python.utils.logging import log


def unique(values):
    new_values = []
    for value in values:
        if value not in new_values:
            new_values.append(value)

    return new_values


# https://stackoverflow.com/questions/66030444/dealing-with-lack-of-non-null-assertion-operator-in-python
T = TypeVar("T")


def not_none(obj: Optional[T]) -> T:
    assert obj is not None
    return obj


L = TypeVar("L")


# NOTE: python appears to not yet support recursive types
NestedList: TypeAlias = list[Union["NestedList[L]", L]]


def flatten(lst: NestedList[L]) -> list[L]:
    # def flatten(lst: List[Any]) -> List:
    flattened_list: list[L] = []
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

    # NOTE exit is still called even if an exception is raised
    def __exit__(self, _type, _value, _traceback):
        elapsed = perf_counter() - self.time
        log.debug(f"{self.msg} took {elapsed:.3f} seconds")


# TODO add decorator for log_execution_time

# TODO add context manager for profiling
"""
    # ob = cProfile.Profile()
    # ob.enable()
    with log_execution_time("schema build"):
        table_schema_limited_by_token_size = SchemaBuilder(engine).build(data_source_id, ranked_structure)
    # ob.disable()
    # sec = io.StringIO()
    # sortby = SortKey.CUMULATIVE
    # ps = pstats.Stats(ob, stream=sec).sort_stats(sortby)
    # ps.print_stats()

    # print(sec.getvalue())
"""
