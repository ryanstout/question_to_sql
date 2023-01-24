import click

from python.questions import question_with_data_source_to_sql
from python.schema.ranker import Ranker
from python.schema.schema_builder import SchemaBuilder

# from python.setup import log


@click.command()
@click.option("--data-source-id", type=int)
@click.option("--question", type=str)
def cli(data_source_id, question):
    sql = question_with_data_source_to_sql(data_source_id, question)
    print(sql)


if __name__ == "__main__":
    cli()
