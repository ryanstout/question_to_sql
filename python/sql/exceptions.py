"""
Exceptions used when parsing and inspecting SQL.
"""


class TableNotFoundException(Exception):
    pass


class ColumnNotFoundException(Exception):
    pass
