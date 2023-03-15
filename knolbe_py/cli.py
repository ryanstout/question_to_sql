import click

import python.utils.functional as f
from python.importer import Importer
from python.query_runner.snowflake import get_query_results, get_snowflake_cursor
from python.questions import question_with_data_source_to_sql
from python.utils.db import application_database_connection
from python.utils.sql import normalize_fqn_quoting


def table_output_with_format(array_of_dicts, table_format="md"):
    if not array_of_dicts:
        return None

    if table_format == "md":
        return markdown_table_output(array_of_dicts)

    return csv_table_output(array_of_dicts)


def markdown_table_output(array_of_dicts, headers: str | list[str] = "keys"):
    # TODO would be nice to add comma separators to money values
    # note all table formats allow float formatting
    from tabulate import tabulate

    return tabulate(array_of_dicts, headers=headers, tablefmt="github", floatfmt=".2f")


def csv_table_output(array_of_dicts):
    import csv
    import sys

    # TODO return CSV as a string
    writer = csv.writer(sys.stdout)
    writer.writerow(array_of_dicts[0].keys())
    writer.writerows([row.values() for row in array_of_dicts])


@click.group(help="internal CLI tools")
# TODO this must be specified before the subcommand, which is a strange requirement. I wonder if there is a way around this.
@click.option("--verbose", "-v", is_flag=True, default=False, help="Enables verbose mode")
def cli(verbose):
    if verbose:
        # bot.utils.setLevel("DEBUG")
        pass


# TODO this is hacky and broken, we need to decide on a functional library
@cli.command(help="Inspect a data source before importing")
@click.option("--data-source-id", required=True, type=int)
@click.option("--warehouse-name", type=str)
@click.option("--database-name", type=str)
@click.option("--schema-name", type=str)
def analysis(data_source_id: int, warehouse_name: str, database_name: str, schema_name: str) -> None:
    db = application_database_connection()

    data_source = db.datasource.find_first(where={"id": data_source_id})
    assert data_source is not None

    cursor, _ = get_snowflake_cursor(data_source, without_context=True)

    if not warehouse_name:
        # In [86]: warehouse_list[0].keys()
        # Out[86]: dict_keys(['name', 'state', 'type', 'size', 'running', 'queued', 'is_default', 'is_current', 'auto_suspend', 'auto_resume', 'available', 'provisioning', 'quiescing', 'other', 'created_on', 'resumed_on', 'updated_on', 'owner', 'comment', 'resource_monitor', 'actives', 'pendings', 'failed', 'suspended', 'uuid'])
        warehouse_list = get_query_results(cursor, "SHOW WAREHOUSES", disable_query_protections=True)

        match len(warehouse_list):
            case 0:
                click.echo("no warehouses")
                return
            case 1:
                warehouse = warehouse_list[0]
                warehouse_name = warehouse["name"]
                click.echo(f"only a single warehouse, selecting: {warehouse_name}")
            case _:
                click.echo("multiple warehouses, please pick ")
                warehouse_headers = ["name", "state"]
                click.echo(
                    markdown_table_output(list(f.pluck(warehouse_headers, warehouse_list)), headers=warehouse_headers)
                )
                return

    cursor.execute(f"use warehouse {warehouse_name};")

    if not database_name:
        click.echo("\n\n# DATABASE LIST\n\n")
        database_list = get_query_results(cursor, "SHOW TERSE DATABASES", disable_query_protections=True)
        click.echo(markdown_table_output(database_list))

    if not schema_name:
        # In [47]: schema_list[0].keys()
        # Out[47]: dict_keys(['created_on', 'name', 'is_default', 'is_current', 'database_name', 'owner', 'comment', 'options', 'retention_time'])
        schema_list = get_query_results(cursor, "SHOW TERSE SCHEMAS", disable_query_protections=True)
        click.echo("\n\n# SCHEMA LIST\n\n")
        click.echo(markdown_table_output(schema_list))

    if not (database_name and schema_name):
        click.echo("need database & schema name to continue")
        return

    click.echo(f"selecting database & schema: {database_name}.{schema_name}")
    cursor.execute(f"use {database_name}.{schema_name};")

    table_list = get_query_results(cursor, "SHOW TERSE TABLES", disable_query_protections=True)

    click.echo("\n\n# TABLE LIST\n\n")
    click.echo(f"Total count: {len(table_list)}\n\n")
    click.echo(markdown_table_output(table_list))

    # the INFORMATION_SCHEMA is really valuable! It caches row count data, and a bunch of other stuff
    # https://stackoverflow.com/questions/59058877/query-to-get-the-row-counts-of-all-the-tables-in-a-database-in-snowflake
    row_count_by_table = get_query_results(
        cursor,
        f"""
        SELECT table_name, row_count
        FROM {database_name}.INFORMATION_SCHEMA.TABLES
        WHERE table_schema = '{schema_name}'
        ORDER BY ROW_COUNT
        """,
        disable_query_protections=True,
    )

    click.echo("\n\n# TABLE COUNT\n\n")
    click.echo(markdown_table_output(row_count_by_table))

    table_names = [table["TABLE_NAME"] for table in row_count_by_table]
    for name in table_names:
        fqn = normalize_fqn_quoting(f"{database_name}.{schema_name}.{name}")
        table_description = get_query_results(cursor, f"DESCRIBE TABLE {fqn}", disable_query_protections=True)
        click.echo(f"\n\n# TABLE DESCRIPTION: {name}\n\n")
        click.echo(markdown_table_output(table_description))


@cli.command(help="create a vector index and related tables from a datasource")
@click.option("--data-source-id", type=int, required=True)
@click.option("--table-limit", type=int)
@click.option("--column-limit", type=int)
@click.option("--column-value-limit", type=int)
def import_datasource(**kwargs):
    Importer(**kwargs)


@cli.command(help="convert a natural language question to sql")
@click.option("--data-source-id", type=int, required=True)
@click.option("--question", type=str, required=True)
def question(data_source_id, question_text):
    sql = question_with_data_source_to_sql(data_source_id, question_text)
    click.echo(sql)


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter
