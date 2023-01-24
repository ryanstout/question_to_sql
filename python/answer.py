from python.setup import log

import click

from python.questions import question_with_data_source_to_sql


@click.command()
@click.option("--data-source-id", type=int, required=True)
@click.option("--question", type=str, required=True)
def cli(data_source_id, question):
    sql = question_with_data_source_to_sql(data_source_id, question)
    print(sql)


if __name__ == "__main__":
    cli()
