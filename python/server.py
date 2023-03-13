import os

from flask import Flask, jsonify, request

from python.query_runner import run_query
from python.questions import question_with_data_source_to_sql
from python.utils.environments import is_production
from python.utils.logging import log
from python.utils.sentry import configure_sentry

application = Flask(__name__)
from decouple import config

# TODO import with side effects! is there a better way to do this?
# TODO this seems to break depending on the location it's put in (i.e. is something else overriding excepthook)
configure_sentry()


@application.route("/healthcheck", methods=["GET"])
def healthcheck():
    return jsonify({})


# TODO this doesn't work...
@application.route("/import", methods=["POST"])
def import_data_source():
    json_data = request.get_json()
    assert json_data is not None

    unused_data_source_id = json_data["data_source_id"]
    return jsonify({})


@application.route("/question", methods=["POST"])
def question():
    json_data = request.get_json()
    assert json_data is not None

    question_text = json_data["question"]
    data_source_id = json_data["data_source_id"]

    engine = "code-davinci-002"
    if config("USE_CHATGPT_MODEL", default=False, cast=bool):
        engine = "gpt-3.5-turbo"

    sql = question_with_data_source_to_sql(data_source_id, question_text, engine=engine)

    return jsonify({"question": question_text, "data_source_id": data_source_id, "sql": sql})


@application.route("/query", methods=["POST"])
def query():
    json_data = request.get_json()
    assert json_data is not None

    sql = json_data["sql"]
    data_source_id = json_data["data_source_id"]
    allow_cached_queries = json_data["allow_cached_queries"]

    results = run_query(data_source_id, sql, allow_cached_queries=allow_cached_queries)

    return jsonify({"sql": sql, "results": results})


if __name__ == "__main__":
    log.info("starting server")
    application.run(debug=not is_production())
