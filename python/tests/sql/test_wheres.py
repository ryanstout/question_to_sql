from python.sql.sql_inspector import SqlInspector


def test_where():
    inspector = SqlInspector(
        """
        SELECT col1 FROM table1 where col2='value1';
        """,
        {"table1": {"name": "table1", "columns": {"col1": {"name": "col1"}, "col2": {"name": "col2"}}}},
    )
    assert inspector.touches() == {
        ("table1", None, None): 1,
        ("table1", "col2", None): 1,
        ("table1", "col2", "value1"): 1,
        ("table1", "col1", None): 1,
    }
