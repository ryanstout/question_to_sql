from pprint import pprint
from typing import List

from deepmerge import always_merger as deep
from sqlglot import exp, parse, parse_one, transpile
from sqlglot.optimizer import optimize
from sqlglot.optimizer.qualify_columns import qualify_columns
from sqlglot.optimizer.qualify_tables import qualify_tables


class SqlTouchPoints:
    def __init__(self):
        pass

    def extract(self, sql: str):
        ast = parse_one(sql, "snowflake")

        metadata = self.walk(ast)
        pprint(metadata)

    def walk(self, node: exp.Expression):
        metadata = {}

        merge = lambda a: deep.merge(metadata, a)

        # print(f"Walk: {node = }")
        match node:
            case exp.Select(args=args) as select:
                print(f"Args: {args = }")
                for key, value in args.items():
                    metadata = merge(self.walk(value))
            # case exp.TableAlias(args={"this": exp.Expression(args=table), "alias"}) as table_alias:
            case exp.Table(args={"this": exp.Identifier(args={"this": table_identifier})}) as table:
                table_alias = None
                match table.args:
                    case {"alias": exp.TableAlias(args={"this": exp.Identifier(args={"this": table_alias})})}:
                        pass

                # If no alias is specified, use the full name
                table_alias = table_alias or table_identifier
                metadata = merge({"tables": {table_alias: [table_identifier]}})

            case exp.Alias(
                args={
                    "this": exp.Expression(args=source_args) as source,
                    "alias": exp.Identifier(args={"this": identifier}),
                }
            ) as alias:

                child_metadata = {"cols": []}
                for key, value in source_args.items():
                    child_metadata = deep.merge(child_metadata, self.walk(value))

                print(f"Alias: {identifier = } {source = }, {child_metadata = }\n\n")

                metadata = merge({"aliases": {identifier: child_metadata["cols"]}})
            case exp.Column(args={"this": exp.Identifier(args={"this": identifier})}) as column:
                alias = column.args.get("alias")
                table_alias = column.args.get("table_alias")
                print(f"COLUMN: {column = } {identifier = } {alias = }")

                # The exp.Column may have a table identifier in front, which
                # can be the table name or an alias
                table_alias = None
                match column.args:
                    case {"table": exp.Identifier(args={"this": table_alias})}:
                        pass

                # If the alias isn't set, use the identifier
                col_alias = alias or identifier
                metadata = merge({"cols": {col_alias: [(identifier, alias, table_alias)]}})
            case exp.Expression(args=args) as expression:
                for key, value in args.items():
                    metadata = merge(self.walk(value))
            case [*expressions]:
                for expr in expressions:
                    metadata = merge(self.walk(expr))
            case _:
                pass

        metadata = self.associate(metadata)

        return metadata

    def associate(self, metadata):
        merge = lambda a: deep.merge(metadata, a)

        # Takes in metadata on the query and associates aliases with columns
        # when possible. This works recursively when unwinding so resolution
        # is done on the nearest alias.

        # Loop through columns, trying to resolve the unresolved columns
        if "cols" in metadata:
            for col_alias, col_info in metadata["cols"].items():
                for col_id, col_alias, table_alias in col_info:
                    if "tables" in metadata:
                        tables = metadata["tables"]
                        if table_alias in tables:
                            last_table_identifier = table_alias[-1]

        return metadata


def table_and_columns_for_sql(sql: str) -> List[List[str]]:
    # Takes a SQL query and returns a list of tables and columns used in the
    # query
    ast = parse_one(sql, "snowflake")

    ast2 = optimize(ast, rules=[qualify_tables, qualify_columns])
    ast = ast2
    print("AST: ", ast)

    table_and_cols = []

    def walk_ast_node(node):
        if isinstance(node, exp.Column):
            col_identifier = node.args["this"]
            assert isinstance(col_identifier, exp.Identifier)
            col_name = col_identifier.args["this"]
            print(f"NODE: {col_name = } {node = }\n\n-- {col_identifier.parent.parent.parent = }")

            col_table_identifier = node.args.get("table")
            if col_table_identifier:
                col_table_alias = col_table_identifier.args["this"]
            else:
                col_table_alias = None

            # Now extract the table
            select = node.parent_select

            from_clause = select.args["from"].args["expressions"]

            table_assocs = {}
            for from_expr in from_clause:
                print(f"FROM: {from_expr = }")
                table_identifier = from_expr.args["this"].args["this"]
                table_alias = from_expr.args.get("alias")
                print("ALIAS: ", table_alias)
                table_assocs[table_alias or table_identifier] = table_identifier

            print(f"TABLE ASSOCS: {table_assocs = }")
            # Lookup the column by its table name or alias
            col_table = None
            if col_table_alias:
                print(f"{table_assocs = }")
                col_table = table_assocs[col_table_alias]
            else:
                if len(table_assocs) == 1:
                    # Only a single table in the FROM clause
                    print(f"Grab first from: {table_assocs = } for {col_name}")
                    col_table = list(table_assocs.values())[0]
                else:
                    raise Exception(f"Couldn't resolve table for column: {col_name}/{col_table_alias}")

            # print("TableCol: ", table_name, column_name)

            table_and_cols.append([col_table, col_name])

        return node

    ast.transform(walk_ast_node)

    return table_and_cols
