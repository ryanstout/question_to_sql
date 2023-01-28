# Run all of the questions marked correct or incorrect and output a confusion
# matrix and accracy

import random
import time
from multiprocessing.pool import ThreadPool
from threading import Lock

from prisma.enums import FeedbackState
from tqdm import tqdm

import python.questions as questions
from python.utils.connections import Connections
from python.utils.logging import log
from python.utils.query_runner import run_query, setup_query_env

THREAD_POOL_SIZE = 1


class Validator:
    def run(self):
        log.info("Running validator")
        self.lock = Lock()
        self.connections = Connections()
        self.connections.open()

        self.thread_pool = ThreadPool(processes=THREAD_POOL_SIZE)

        self.scores = {}
        self.failed_questions = []

        db = self.connections.db

        self.data_source_id = 1  # stub for now

        # Run through each marked question
        db_questions = db.question.find_many(
            where={"feedbackState": FeedbackState.CORRECT}, include={"questionGroup": {"include": {"questions": True}}}, take=5
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

        log.info("Scores: ", scores=self.scores)
        # for failed_question in self.failed_questions:
        #     log.info("Failed question: ", q=failed_question)
        log.info("Percent match: ", percent_match=percent_match)

    def process_correct_question(self, idx_correct_question) -> None:
        idx = idx_correct_question[0]
        correct_question = idx_correct_question[1]

        # 60 second jitter so all of the requests don't come in at once
        # log.info(f"[{idx}] Sleeping for jitter")
        # time.sleep(random.random() * 60)
        # log.info(f"[{idx}] Run question: {correct_question.question}")

        snowflake_cursor = self.connections.snowflake_cursor()
        setup_query_env(snowflake_cursor)

        old_sql = correct_question.userSql
        log.debug("Old SQL: ", old_sql=old_sql)

        old_results = run_query(snowflake_cursor, old_sql)
        if "error" in old_results:
            # Query returned an error
            log.error("Error running old query: ", sql=old_sql, results=old_results)
            self.set_scores(correct_question.id, 0, correct_question.question)

            return None

        for question in correct_question.questionGroup.questions:
            log.info(f"[{idx}] Send to openai")
            t1 = time.time()
            new_sql = questions.question_with_data_source_to_sql(self.data_source_id, question.question)
            t2 = time.time()
            log.info(f"[{idx}] Got from openai in ", time=t2 - t1)
            log.debug("new sql", new_sql=new_sql)
            new_results = run_query(snowflake_cursor, new_sql)

            if "error" in new_results:
                # Query returned an error
                log.error("Error running new query: ", sql=new_sql, results=new_results)
                self.set_scores(question.id, 0, question.question)
                continue

            if self.check_match(old_results, new_results):
                log.info(f"[{idx}] Results match")
                self.set_scores(question.id, 1, question.question)
            else:
                log.info(f"[{idx}] Results don't match")
                self.set_scores(question.id, 0, question.question)

        return None

    def set_scores(self, question_id: int, score: int, question: str):
        self.lock.acquire()
        self.scores[question_id] = score
        self.failed_questions.append(question)
        self.lock.release()

    def check_match(self, old_results, new_results):
        # Because the column names may differ each run, we match based on output
        # columns.
        # log.info("old vs new all", old=old_results, new=new_results)

        # Loop through each column in both and make sure the key/values match
        for idx, old_result in enumerate(old_results):
            # The column names may differ, we really just care if we get columns
            # with the same values, so pull the values without the keys (column
            # names), then sort so the ordering is the same
            if idx >= len(new_results):
                log.info("Old results had more results")
                return False
            new_result = new_results[idx]
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
