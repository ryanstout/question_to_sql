from flask import Flask, jsonify, request

from python.questions import question_with_data_source_to_sql

app = Flask(__name__)
from python.setup import log


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


if __name__ == "__main__":
    log.info("starting server")
    app.run()
