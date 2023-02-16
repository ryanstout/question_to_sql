import pytest

from python.sql.exceptions import FilterNotSupportedError
from python.sql.sql_inspector import SqlInspector


def test_filter_unsupported():
    with pytest.raises(FilterNotSupportedError):
        inspector = SqlInspector(
            """
            SELECT SUM(col1) FILTER(WHERE col1 > 100) as sum_col1 FROM table1;
            """,
            {"table1": ["col1"]},
            dialect="snowflake",
        )

    inspector = SqlInspector(
        """
        SELECT (SUM(col1) FILTER(WHERE col1 > 100)) as sum_col1 FROM table1;
        """,
        {"table1": ["col1"]},
        dialect="postgres",
    )
