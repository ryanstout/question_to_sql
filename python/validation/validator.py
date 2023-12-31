# Run all of the questions marked correct or incorrect and output a confusion
# matrix and accracy

import json
import os
import shutil
from multiprocessing.pool import ThreadPool
from threading import Lock
from typing import Tuple

import sentry_sdk
from decouple import config

import python.questions as questions
from python import utils
from python.query_runner.snowflake import run_snowflake_query
from python.utils.logging import log

from prisma.enums import EvaluationStatus
from prisma.models import DataSource, EvaluationQuestionGroup

THREAD_POOL_SIZE = 1

# TODO this shares a global db connection, may cause issues with threading
db = utils.db.application_database_connection()

# Run all of the questions marked correct or incorrect and output a confusion
# matrix and accuracy
class Validator:
    data_source: DataSource

    def __init__(self):
        self.lock = Lock()
        self.thread_pool = ThreadPool(processes=THREAD_POOL_SIZE)

        self.scores = {}
        self.failed_questions = []

        log_records_path = config("VALIDATION_PATH")
        if not isinstance(log_records_path, str):
            raise ValueError("VALIDATION_PATH must be set")

        self.log_records_path = log_records_path

    def run(self):
        shutil.rmtree(self.log_records_path, ignore_errors=True)
        os.makedirs(f"{self.log_records_path}/correct", exist_ok=True)
        os.makedirs(f"{self.log_records_path}/incorrect", exist_ok=True)

        # Run through each marked question
        db_questions = db.evaluationquestiongroup.find_many(
            where={"status": EvaluationStatus.CORRECT},
            include={"evaluationQuestions": True, "dataSource": True},
            order={"id": "asc"},
        )

        # Load each question in the group, and assume the question

        tasks = []

        self.thread_pool.map(self.process_correct_question, enumerate(db_questions))
        # for idx, correct_question in tqdm(enumerate(db_questions)):
        #     # Look up the questionGroup and test each question to see if
        #     # we are now generating the right sql
        #     self.thread_pool.apply_async(
        #         self.process_correct_question,
        #         args=(
        #             idx,
        #             correct_question,
        #         ),
        #     )

        self.thread_pool.close()
        self.thread_pool.join()

        # Call get on futures to make sure we re-raise any exceptions
        for task in tasks:
            task.get()

        score_length = len(self.scores)

        percent_match = sum(self.scores.values()) / score_length

        log.info("scores", scores=self.scores)
        # for failed_question in self.failed_questions:
        #     log.info("failed question", q=failed_question)
        log.info("percent match", percent_match=percent_match)

    def process_correct_question(self, idx_and_evaluation_group: Tuple[int, EvaluationQuestionGroup]) -> None:
        idx = idx_and_evaluation_group[0]
        evaluation_group = idx_and_evaluation_group[1]

        data_source = evaluation_group.dataSource
        correct_sql = evaluation_group.correctSql
        evaluation_questions = evaluation_group.evaluationQuestions

        if not data_source:
            log.error("No data source found for question group", evaluation_group=evaluation_group)
            return None

        if not correct_sql:
            log.error("No sql found for question group", evaluation_group=evaluation_group)
            return None

        if not evaluation_questions:
            log.error("No questions found for question group", evaluation_group=evaluation_group)
            return None

        log.debug("Correct SQL: ", correct_sql=correct_sql)

        try:

            old_results = run_snowflake_query(data_source, correct_sql)
            if "error" in old_results:
                # Query returned an error
                log.error("Error running old query: ", sql=correct_sql, results=old_results)
                self.set_scores(evaluation_group.id, 0, None)

                return None

            for question in evaluation_questions:
                correct = False
                new_results = None
                new_sql = ""
                try:
                    log.info(f"[{idx}] send to openai")
                    new_sql = questions.question_with_data_source_to_sql(data_source.id, question.question)
                    log.debug("new sql", new_sql=new_sql)
                    new_results = run_snowflake_query(data_source, new_sql)

                    if "error" in new_results:
                        # Query returned an error
                        log.error("Error running new query: ", sql=new_sql, results=new_results)
                        self.set_scores(question.id, 0, question.question)
                        continue

                    if check_match(old_results, new_results):
                        log.info(f"[{idx}] results match", question_id=question.id)
                        self.set_scores(question.id, 1, question.question)
                        correct = True
                    else:
                        log.info(f"[{idx}] results don't match", question_id=question.id)
                        self.set_scores(question.id, 0, question.question)

                except Exception as e:
                    sentry_sdk.capture_exception(e)
                    # Some exception happened when generating or running the query, log it and fail the group
                    log.debug("Error running question", question=question.question, e=e)
                    self.set_scores(evaluation_group.id, 0, None)

                correct_folder = "correct" if correct else "incorrect"
                base_path = f"{self.log_records_path}/{correct_folder}/{question.id}"
                # Log out the generated sql and results
                self._log(f"{base_path}_question.txt", question.question)

                self._log(f"{base_path}_old.sql", correct_sql)
                self._log(f"{base_path}_new.sql", new_sql)

                self._log(f"{base_path}_old.json", json.dumps(old_results, indent=2))
                self._log(f"{base_path}_new.json", json.dumps(new_results, indent=2))

                os.system(f"diff {base_path}_old.json {base_path}_new.json > {base_path}.json.diff")

        except Exception as e:
            sentry_sdk.capture_exception(e)
            # Some exception happened when generating or running the query, log it and fail the group
            log.debug("Error running query", e=e)
            self.set_scores(evaluation_group.id, 0, None)

        return None

    def set_scores(self, question_id: int, score: int, question: str | None):
        self.lock.acquire()
        self.scores[question_id] = score
        if question:
            self.failed_questions.append(question)
        self.lock.release()

    def _log(self, path: str, text: str):
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)


def check_match(old_results, new_results):
    # Because the column names may differ each run, we match based on output
    # columns.
    # log.info("old vs new all", old=old_results, new=new_results)

    # Loop through each column in both and make sure the key/values match
    for idx, old_result in enumerate(old_results):
        # The column names may differ, we really just care if we get columns
        # with the same values, so pull the values without the keys (column
        # names), then sort so the ordering is the same
        if idx >= len(new_results):
            log.info("old results had more results")
            return False

        # Grab the same row
        new_result = new_results[idx]

        # Sort the column values so column order doesn't matter
        new_result_vals = list([str(v) for v in new_result.values()])
        old_result_vals = list([str(v) for v in old_result.values()])

        new_result_vals.sort()
        old_result_vals.sort()

        if new_result_vals != old_result_vals:
            log.error("Results don't match", old=old_result, new=new_result)

            return False

    return True


if __name__ == "__main__":
    Validator().run()
