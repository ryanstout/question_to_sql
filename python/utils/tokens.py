import tiktoken

from python.utils.openai import openai_engine

engine = openai_engine()
if engine in ["gpt-4", "gpt-4-32k"]:
    # No support for gpt-4 in tiktoken yet
    engine = "gpt-3.5-turbo"

# Only load the encoder once
token_encoder = tiktoken.encoding_for_model(engine)


def count_tokens(text: str) -> int:
    return len(token_encoder.encode(text))
