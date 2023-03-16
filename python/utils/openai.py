import typing as t

from decouple import config

from python.utils.logging import log

OpenAIEngineOptions = t.Literal["gpt-3.5-turbo", "gpt-4", "gpt-4-32k", "code-davinci-002"]
# leaked chatgpt model: text-chat-davinci-002-20230126

OPENAI_DEFAULT_ENGINE: OpenAIEngineOptions = "code-davinci-002"


def is_chat_engine(engine: OpenAIEngineOptions) -> bool:
    return engine in ["gpt-3.5-turbo", "gpt-4", "gpt-4-32k"]


def openai_engine() -> OpenAIEngineOptions:
    if config("USE_CHATGPT_MODEL", default=False, cast=bool):
        log.debug("using chat model")
        # return "gpt-3.5-turbo"
        return "gpt-4"

    return OPENAI_DEFAULT_ENGINE
