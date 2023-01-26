# Run all of the questions marked correct or incorrect and output a confusion
# matrix and accracy

from prisma.enums import FeedbackState

import python.questions as questions
from python.utils.connections import Connections
from python.utils.logging import log
from python.utils.query_runner import run_query, setup_query_env


class Validator:
    def run(self):
        log.info("Running validator")
        connections = Connections()
        connections.open()

        scores = {}

        db = connections.db

        data_source_id = 1  # stub for now

        # Run through each marked question
        db_questions = db.question.find_many(where={"feedbackState": FeedbackState.CORRECT}, include={"questionGroup": {"questions": True}})

        # Load each question in the group, and assume the question

        snowflake_cursor = connections.snowflake_cursor()
        setup_query_env(snowflake_cursor)

        for correct_question in db_questions:
            # Look up the questionGroup and test each question to see if
            # we are now generating the right sql

            old_sql = correct_question.codexSql

            old_results = run_query(snowflake_cursor, old_sql)

            for question in correct_question.question_group.questions:
                new_sql = questions.question_with_data_source_to_sql(data_source_id, question.question)
                print(new_sql)
                new_results = run_query(snowflake_cursor, new_sql)

                if self.check_match(old_results, new_results):
                    log.info("Results match")
                    scores[question.id] = 1
                else:
                    scores[question.id] = 0

        percent_match = sum(scores.values()) / len(scores)

        log.info("Scores: ", scores=scores)
        log.info("Percent match: ", percent_match=percent_match)

    def check_match(self, old_results, new_results):
        # Because the column names may differ each run, we match based on output
        # columns.
        # log.info("old vs new all", old=old_results, new=new_results)

        # Loop through each column in both and make sure the key/values match
        for idx, old_result in enumerate(old_results):
            # The column names may differ, we really just care if we get columns
            # with the same values, so pull the values without the keys (column
            # names), then sort so the ordering is the same
            new_result = list(new_results[idx].values())
            old_result = list(old_result.values())

            new_result.sort()
            old_result.sort()

            log.info("old vs new", old=old_result, new=new_result)

            if new_result != old_result:
                log.error("Results don't match", old=old_result, new=new_result)

                return False

        return True


if __name__ == "__main__":
    Validator().run()
