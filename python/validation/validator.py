# Run all of the questions marked correct or incorrect and output a confusion
# matrix and accracy

from prisma.enums import FeedbackState

import python.questions as questions
from python.utils.connections import Connections
from python.utils.query_runner import run_query


class Validator:
    def run(self):
        connections = Connections()
        connections.open()

        db = connections.db

        data_source_id = 1  # stub for now

        # Run through each marked question
        db_questions = db.question.find_many(
            where={
                "OR": [
                    {"feedbackState": FeedbackState.CORRECT},
                    {"feedbackState": FeedbackState.INCORRECT},
                ]
            }
        )

        snowflake_cursor = connections.snowflake_cursor()
        snowflake_cursor.execute("use warehouse COMPUTE_WH;")

        for question in db_questions:
            old_sql = question.codexSql

            old_results = run_query(snowflake_cursor, old_sql)
            print(old_results)

            new_sql = questions.question_with_data_source_to_sql(data_source_id, question.question)
            # new_results = snowflake_cursor.execute(new_sql)

    def check_match(self, old_results, new_results):
        # Because the column names may differ each run, we match based on output
        # columns.
        pass


if __name__ == "__main__":
    Validator().run()
