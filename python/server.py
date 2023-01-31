from python.setup import log

from flask import Flask, jsonify, request

from python.query_runner import run_query
from python.questions import question_with_data_source_to_sql
from python.utils.system import is_production

app = Flask(__name__)


@app.route("/healthcheck", methods=["GET"])
def healthcheck():
    return jsonify({})


@app.route("/import", methods=["POST"])
def import_data_source():
    json_data = request.get_json()
    data_source_id = json_data["data_source_id"]
    return jsonify({})


@app.route("/question", methods=["POST"])
def question():
    json_data = request.get_json()

    question = json_data["question"]
    data_source_id = json_data["data_source_id"]

    sql = question_with_data_source_to_sql(data_source_id, question)

    return jsonify({"question": question, "data_source_id": data_source_id, "sql": sql})


@app.route("/query", methods=["POST"])
def query():
    json_data = request.get_json()

    sql = json_data["sql"]
    data_source_id = json_data["data_source_id"]

    results = run_query(data_source_id, sql)

    return jsonify({"sql": sql, "results": results})


if __name__ == "__main__":
    log.info("starting server")
    app.run(debug=(not is_production()))
