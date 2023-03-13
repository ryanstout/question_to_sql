import sqlglot
from sqlglot import exp, parse_one

from python.prompts.few_shot_example import FewShotExample
from python.schema.ranker import ElementRank
from python.schema.simple_schema_builder import build_simple_schema
from python.sql.sql_parser import SqlParser
from python.utils.db import application_database_connection
from python.utils.indexes_and_models import application_indexes_and_models

db = application_database_connection()
indexes_and_models = application_indexes_and_models()


def revert_sql_for_few_shot(sql: str) -> str:
    # Use sqlglot to lowercase the table and column names (since sometimest hey get saved capitalized)

    # Transpile from snowflake back to postgres
    sqlglot.transpile(sql, read=SqlParser.out_dialect, write=SqlParser.in_dialect)

    expr = parse_one(sql, read=SqlParser.in_dialect)

    def transformer(node):
        if isinstance(node, exp.Identifier):
            node.args["this"] = node.args["this"].lower()
        return node

    transformed_tree = expr.transform(transformer)
    return transformed_tree.sql(pretty=True, max_text_width=40) + ";"


class FewShot:
    def __init__(self, data_source_id: int, is_chat: bool, comments: str, backticks: str, question_prefix: str):
        self.data_source_id = data_source_id
        self.comments = comments
        self.backticks = backticks
        self.question_prefix = question_prefix
        self.is_chat = is_chat

    def generate(self, current_question: str) -> tuple[list[str], list[str], list[ElementRank]]:
        # Find similar questions to use as few shot examples
        ids = indexes_and_models.few_shot(self.data_source_id).search(current_question, 3)

        rankings: list[ElementRank] = []
        sql_queries: list[str] = []
        prompt_examples = []

        simple_schema = build_simple_schema(self.data_source_id)

        for question_id in ids:
            question = db.evaluationquestion.find_unique({"id": question_id}, include={"evaluationQuestionGroup": True})

            if question:
                correct_sql = question.evaluationQuestionGroup and question.evaluationQuestionGroup.correctSql

                if correct_sql:
                    correct_sql = revert_sql_for_few_shot(correct_sql)

                    example = FewShotExample(self.data_source_id, simple_schema, correct_sql)

                    rankings += example.schema_rankings
                    sql_queries.append(correct_sql)
                    if self.is_chat:
                        prompt_examples.append(f"{self.question_prefix}{question.question}")
                    else:
                        prompt_examples += [
                            f"{self.comments}{self.question_prefix}{question.question}",
                            f"{self.backticks}{correct_sql}{self.backticks}",
                            "",
                            "",
                        ]

        return (prompt_examples, sql_queries, rankings)

    def generate_old(self) -> list[str]:
        few_shot = [
            f"{self.comments}{self.question_prefix}How many orders are there per month?",
            f"""{self.backticks}SELECT
  COUNT(*) AS orders_per_month,
  EXTRACT(MONTH FROM "order".created_at) AS month
FROM "order"
GROUP BY
  month
ORDER BY
  month;{self.backticks}""",
            "",
            "",
            f"{self.comments}{self.question_prefix}Question: Which product sells the best?",
            f"""{self.backticks}SELECT
    COUNT(*) AS orders_per_product,
    product.title
FROM "order"
JOIN order_line
    ON order_line.order_id = "order".id
JOIN product_variant
    ON product_variant.id = order_line.variant_id
JOIN product
    ON product.id = product_variant.product_id
GROUP BY
    product.id,
    product.title
ORDER BY
orders_per_product DESC;{self.backticks}
            """,
            "",
            f"{self.comments}{self.question_prefix}Are sales of the cross atx fountain pen - matte chrome increasing or decreasing?",
            f"""{self.backticks}SELECT
    COUNT(*) AS orders_per_month,
    EXTRACT(MONTH FROM "ORDER".created_at) AS month
FROM "order"
JOIN order_line
    ON order_line.order_id = "order".id
JOIN product_variant
    ON product_variant.id = order_line.variant_id
JOIN product
    ON product.id = product_variant.product_id
WHERE
    product.title = 'Cross ATX Fountain Pen - Matte Chrome'
GROUP BY
    month
ORDER BY
    month;{self.backticks}""",
            "",
            "",
            f"""{self.comments}{self.question_prefix}What products are pen and pencil sets""",
            f"""{self.backticks}SELECT DISTINCT
  product.title
FROM product
JOIN product_tag
  ON product_tag.product_id = product.id
WHERE
  product_tag.value = 'Collection_Pen and Pencil Set'
ORDER BY
  product.title;{self.backticks}""",
            "",
            "",
        ]

        return few_shot
