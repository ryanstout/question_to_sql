import pytest


@pytest.mark.vcr()
def test_basic_answer(client):
    original_question = "What is the id of the first customer created?"

    response = client.post(
        "/question",
        json={
            "data_source_id": 1,
            "question": original_question,
            "allow_cached_queries": False,
        },
    )

    breakpoint()

    # TODO this will be brittle, but I'm also curious when it will break
    assert response.json == {
        "data_source_id": 1,
        "question": original_question,
        "sql": "SELECT\n  id\nFROM customer\nORDER BY\n  created_at NULLS LAST\nLIMIT 1",
    }
