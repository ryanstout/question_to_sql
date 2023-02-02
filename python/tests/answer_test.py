def test_basic_answer(client):
    response = client.post(
        "/question",
        json={
            "data_source_id": 1,
            "question": "What is the name of the user with id 2?",
        },
    )

    # TODO this will be brittle, but I'm also curious when it will break
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
