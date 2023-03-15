import pytest

from python.importer import Importer

# TODO this test requires a valid local schema to be in place, which is tied to faise


@pytest.mark.vcr
def test_basic_import(client):
    data_source_id = 1

    Importer(data_source_id=data_source_id, table_limit=1, column_limit=1, column_value_limit=1)

    breakpoint()
