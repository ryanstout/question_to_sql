import tiktoken
from decouple import config

# Only load the encoder once
if config("USE_CHATGPT_MODEL", default=False, cast=bool):
    token_encoder = tiktoken.encoding_for_model("gpt-3.5-turbo")
else:
    token_encoder = tiktoken.encoding_for_model("code-davinci-002")


def count_tokens(text: str) -> int:
    return len(token_encoder.encode(text))
