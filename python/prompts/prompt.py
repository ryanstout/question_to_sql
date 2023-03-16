"""
Provides a class to create prompts based on the user's question and the schema. Since codex and chatgpt models require
different prompt formats, we extract them into seperate classes to generate the correct prompts.
"""


import datetime

from python.prompts.few_shot import FewShot
from python.schema.ranker import SCHEMA_RANKING_TYPE, merge_schema_rankings
from python.schema.schema_builder import SchemaBuilder
from python.sql.sql_parser import SqlParser
from python.utils.db import application_database_connection
from python.utils.logging import log
from python.utils.tokens import count_tokens

db = application_database_connection()


class Prompt:
    # The order of the sections in the prompt can be overridden in child classes
    section_order: list[str] = ["prologue", "schema", "rules", "few_shot", "question"]
    few_shot_generator: FewShot | None
    question_prefix: str
    comments: str
    backticks: str
    used_tokens: int = 0
    ranked_schema: SCHEMA_RANKING_TYPE

    def __init__(
        self,
        engine: str,
        data_source_id: int,
        ranked_schema: SCHEMA_RANKING_TYPE,
        user_question: str,
        use_global_instruct: bool = False,
        use_rules: bool = True,
        use_few_shot: bool = False,
        use_comments: bool = True,
        use_backticks: bool = False,
    ):
        self.engine = engine
        self.data_source_id = data_source_id
        self.ranked_schema = ranked_schema
        self.user_question = user_question
        self.use_global_instruct = use_global_instruct
        self.use_rules = use_rules

        # The tripple backtick wrapper can be useful in some cases
        self.backticks = "```" if use_backticks else ""
        self.comments = "-- " if use_comments else ""

        if use_global_instruct:
            self.question_prefix = "Question: "
        else:
            self.question_prefix = ""

        if use_few_shot:
            self.few_shot_generator = FewShot(
                data_source_id, self.is_chat(), self.comments, self.backticks, self.question_prefix
            )
        else:
            self.few_shot_generator = None

    def is_chat(self):
        return False

    def available_tokens(self) -> int:
        return 8_000 - 1_024

    def generate(self) -> str:
        available_tokens = self.available_tokens()

        sections = {}
        if "prologue" in self.section_order:
            sections["prologue"] = self.prologue()

        if "rules" in self.section_order:
            sections["rules"] = self.rules()

        if "few_shot" in self.section_order:
            sections["few_shot"], _, few_shot_rankings = self.few_shot(self.user_question)

            # Merge the few_shot_rankings into the schema rankings
            self.ranked_schema = merge_schema_rankings(self.ranked_schema, few_shot_rankings)

        if "question" in self.section_order:
            sections["question"] = self.question()

        # Count the used tokens so far
        self.used_tokens = sum([count_tokens("\n".join(section)) for section in sections.values()])

        # Compute the schema using the remaining tokens
        sections["schema"] = self.schema(self.available_tokens() - self.used_tokens)
        print(
            "SCHEMA TOKS: ",
            count_tokens("\n".join(sections["schema"])),
            " AVAILABLE: ",
            self.available_tokens() - self.used_tokens,
        )

        prompt = []

        # Add the sections in the order specified by the section_order attribute
        for section in self.section_order:
            prompt += sections[section]

        final_prompt = "\n".join(prompt)

        token_count = count_tokens(final_prompt)

        if token_count > available_tokens:
            raise ValueError(
                f"Generated prompt is too long, tokens: {token_count}, available: {available_tokens}\n\nPrompt: {final_prompt}"
            )

        log.debug("OpenAI Prompt: ", type=self.__class__, prompt=final_prompt, tokens=token_count)

        return final_prompt

    def prologue(self):
        if self.use_global_instruct:
            return [
                f"{self.comments}Given a Schema, and a Question, generate a correct SQL query that answers the question using the Schema. The SQL query must follow the Rules provided.",
                "",
            ]
        else:
            return []

    def schema(self, available_tokens: int):
        """
        Returns a string represenation of the schema with associated prologue
        """
        schema = SchemaBuilder().build(self.data_source_id, self.ranked_schema, available_tokens)

        return [
            f"{self.comments}Schema: {SqlParser.in_dialect.capitalize()} SQL schema",
            f"{self.backticks}{schema}{self.backticks}",
            "",
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
                f"{self.backticks}",
                # f"{comments}Rules for building SQL queries: ",
                f"{self.comments}Rules: ",
                f"{self.comments}{rule_prefix()}Return `SELECT 'unsure'` if we don't know how to answer the question",
                # f"{self.comments}{rule_prefix()}Do case insensitive matches using LOWER unless the case matters or it matches a possible value",
                f"{self.comments}{rule_prefix()}When matching a string, use LOWER unless it matches a listed possible value",
                # f"{self.comments}{rule_prefix()}Calculate lifetime of a customer by taking the duration between the first and most recent order for a customer. ",
                f"{self.comments}{rule_prefix()}If we're returning a day, always also return the month and year",
                f"{self.comments}{rule_prefix()}Add ORDER BY to every SELECT",  # makes things deterministic
                # In snowflake, Count(*), etc.. are not allowed directly in a ORDER BY or HAVING, they have to be in the
                # SELECT expression first, then accessed by alias.
                # f"{self.comments}{rule_prefix()}COUNT's used in ORDER BY or HAVING should appear in the SELECT first.",
                f"{self.comments}{rule_prefix()}Only alias tables/columns if necessary",
                f"{self.comments}{rule_prefix()}Any columns used must be in the Schema",
                f"{self.comments}{rule_prefix()}Assume the current date is {current_date}",
                f"{self.comments}{rule_prefix()}use NOW() instead of dates",
                f"{self.backticks}",
                "",
            ]
        else:
            rules = []

        return rules

    def few_shot(self, current_question: str) -> tuple[list[str], list[str], SCHEMA_RANKING_TYPE]:
        # The generator will only be present if we've enabled adding few shot
        if self.few_shot_generator:
            return self.few_shot_generator.generate(current_question)

        return ([], [], [])

    def question(self):
        return [
            f"{self.comments}{self.question_prefix}{self.user_question}",
            f"{self.backticks}SELECT ",
        ]
