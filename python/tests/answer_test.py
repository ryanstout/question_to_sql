import pytest

from python.server import application


@pytest.fixture()
def app():
    application.config.update(
        {
            "TESTING": True,
        }
    )

    yield application


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


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
