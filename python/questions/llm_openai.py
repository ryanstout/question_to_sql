# Convert a natural language question to a SQL query based on the schema

import code
import os
import sys
import openai
from prompt import Prompt
from decouple import config

openai.api_key = config("OPENAI_API_KEY")


class LLMOpenai:
    def __init__(self, question: str):

        nlp_question = sys.stdin.read()

        with open("prisma/test_schema.sql", "r") as f:
            test_schema = f.read()

        prompt = Prompt(test_schema, question).text()

        result = openai.Completion.create(
            engine="code-davinci-002",
            prompt=prompt,
            max_tokens=1024,  # was 256
            temperature=0.0,
            top_p=1,
            presence_penalty=0,
            frequency_penalty=0,
            best_of=1,
            n=1,
            stream=False,
            stop=[";", "\n\n"],
        )
