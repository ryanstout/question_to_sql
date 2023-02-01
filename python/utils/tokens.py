import tiktoken

# Only load the encoder once
token_encoder = tiktoken.get_encoding("gpt2")


def count_tokens(text: str) -> int:
    return len(token_encoder.encode(text))
