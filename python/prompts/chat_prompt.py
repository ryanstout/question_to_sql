import datetime
from pprint import pprint

from python.prompts.prompt import Prompt
from python.schema.ranker import SCHEMA_RANKING_TYPE, merge_schema_rankings
from python.schema.schema_builder import SchemaBuilder
from python.sql.sql_parser import SqlParser
from python.utils.db import application_database_connection
from python.utils.logging import log
from python.utils.tokens import count_tokens

db = application_database_connection()


class ChatPrompt(Prompt):
    section_order: list[str] = ["prologue", "few_shot", "question"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.use_global_instruct = True
        self.backticks = "```"
        self.comments = ""

    def available_tokens(self) -> int:
        # extra buffer, since SchemaBuilder doesn't match exactly
        extra_buffer_for_schema_builder = 100
        completion_tokens = 1_024
        return 4_096 - completion_tokens - extra_buffer_for_schema_builder

    def generate(self) -> list[dict]:
        sections = {}
        if "prologue" in self.section_order:
            prologue = self.prologue()
            if len(prologue) > 0:
                prologue = prologue[0]["content"] + "\n\n"
            else:
                prologue = ""

            if self.use_rules:
                rules = self.rules()[0]["content"]
            else:
                rules = ""

            sections["prologue"] = [{"role": "system", "content": f"{prologue}{rules}"}]

        if "few_shot" in self.section_order:
            sections["few_shot"], few_shot_rankings = self.few_shot(self.user_question)

            # Merge the few_shot_rankings into the schema rankings
            self.ranked_schema = merge_schema_rankings(self.ranked_schema, few_shot_rankings)

        if "question" in self.section_order:
            sections["question"] = self.question()

        # Count the used tokens so far
        self.used_tokens = 0
        for section in sections.values():
            contents = map(lambda x: x["content"], section)
            self.used_tokens += sum(map(count_tokens, contents))

        # Compute the schema using the remaining tokens
        sections["prologue"][0]["content"] += "\n\n"
        sections["prologue"][0]["content"] += self.schema(self.available_tokens() - self.used_tokens)[0]["content"]

        prompt = []

        # Add the sections in the order specified by the section_order attribute
        for section in self.section_order:
            prompt += sections[section]

        for line in prompt:
            log.debug("prompt: ", role=line["role"], content=line["content"])

        return prompt

    def prologue(self):
        if self.use_global_instruct:
            return [
                {
                    "role": "system",
                    "content": "You are an expert SQL developer. Given a Schema, and a Question, generate the correct SQL query that answers the users question using the Schema. The SQL query must follow the following Rules.",
                }
            ]
        else:
            return []

    def schema(self, available_tokens: int):
        """
        Returns a messsage represenation of the schema with associated prologue
        """
        schema = SchemaBuilder().build(self.data_source_id, self.ranked_schema, available_tokens)

        return [
            {
                "role": "system",
                "content": "\n".join(
                    [
                        f"Schema: {SqlParser.in_dialect.capitalize()} SQL schema",
                        f"```\n{schema}\n```",
                    ]
                ),
            }
        ]

    def rules(self):
        """
        Rules we provide to the LLM to attempt to get it to do what we want. This will probably work better on chatgpt
        than others, but seems to work in a lot of cases on codex.
        """

        def generate_date_suffix(n):
            if 10 <= n % 100 < 20:
                return "th"

            return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")

        day_int = datetime.datetime.now().day
        suffix = generate_date_suffix(day_int)

        # current date in the format of 'January 28th, 2023'
        # the date format here is picked in a very specific fashion
        current_date = datetime.datetime.now().strftime(f"%B %-d{suffix}, %Y")

        if self.use_rules:
            rule_num: int = 0

            def rule_prefix():
                nonlocal rule_num
                rule_num += 1
                return f"{rule_num}. "

            rules = [
                "",
                # f"{comments}Rules for building SQL queries: ",
                "Rules: ",
                # f"{rule_prefix()}Return `SELECT 'unsure';` if the SQL for the question can not be generated",
                # f"{rule_prefix()}Do case insensitive matches using LOWER unless the case matters or it matches a possible value",
                f"{rule_prefix()}When matching a string, use LOWER or ILIKE unless it matches a listed possible value",
                # f"{rule_prefix()}Calculate lifetime of a customer by taking the duration between the first and most recent order for a customer. ",
                f"{rule_prefix()}If we're returning a day, always also return the month and year",
                f"{rule_prefix()}Add ORDER BY to every SELECT",  # makes things deterministic
                # In snowflake, Count(*), etc.. are not allowed directly in a ORDER BY or HAVING, they have to be in the
                # SELECT expression first, then accessed by alias.
                f"{rule_prefix()}COUNT's used in ORDER BY or HAVING should appear in the SELECT first.",
                # f"{rule_prefix()}Any columns used must be in the Schema",
                f"{rule_prefix()}Assume the current date is {current_date}",
                f"{rule_prefix()}use NOW() instead of dates",
                f"{rule_prefix()}Don't use CTE's",
                # f"{rule_prefix()}Don't alias tables unless necessary",
                # f"{rule_prefix()}GROUP BY clauses should include all fields from the SELECT clause",
                "",
            ]
        else:
            rules = []

        return [
            {
                "role": "system",
                "content": "\n".join(rules),
            }
        ]

    def few_shot(self, current_question: str) -> tuple[list[dict[str, str]], SCHEMA_RANKING_TYPE]:
        # The generator will only be present if we've enabled adding few shot
        if self.few_shot_generator:
            few_shot_examples, correct_sql, schema_rankings = self.few_shot_generator.generate(current_question)

            examples: list[dict[str, str]] = []

            for idx, example in enumerate(few_shot_examples):
                examples.append(
                    {
                        "role": "user",
                        "content": example,
                    }
                )
                examples.append({"role": "assistant", "content": f"```{correct_sql[idx]}```"})

            return (examples, schema_rankings)
        else:
            return ([], [])

    def question(self):
        return [{"role": "user", "content": self.user_question}]

    def is_chat(self):
        return True
