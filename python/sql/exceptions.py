"""
Exceptions used when parsing and inspecting SQL.
"""


class SqlInspectError(Exception):
    pass


class TableNotFoundError(SqlInspectError):
    pass


class ColumnNotFoundError(SqlInspectError):
    pass


class FilterNotSupportedError(SqlInspectError):
    pass


class SqlParseError(SqlInspectError):
    pass
