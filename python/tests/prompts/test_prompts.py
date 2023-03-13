from python.prompts.prompt import Prompt


def test_prompt():
    """Test prompt."""
    prompts = Prompt("code-davinci-002", 1, [], "How many orders are there?")
    result = prompts.generate()

    print(result)

    # Assertions to check that the built prompt string contains expected parts
    assert "How many orders are there?" in result
    assert "Postgres SQL schema" in result
    assert "Rules: " in result
    assert "\nSELECT" in result
