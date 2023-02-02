import pytest

from python.server import application


def test_basic_answer(client):
    response = client.post(
        "/question",
        json={
            "data_source_id": 1,
            "question": "What is the name of the user with id 2?",
        },
    )

    assert response.json == {
        "data_source_id": 1,
        "question": "What is the name of the user with id 2?",
        "sql": "SELECT\n"
        "  CUSTOMER.first_name,\n"
        "  CUSTOMER.last_name\n"
        "FROM CUSTOMER\n"
        "WHERE\n"
        "  CUSTOMER.id = 2",
    }
