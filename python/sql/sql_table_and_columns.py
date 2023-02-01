from typing import List

from sqlglot import exp, parse, parse_one, transpile
from sqlglot.optimizer import optimize
from sqlglot.optimizer.qualify_columns import qualify_columns
from sqlglot.optimizer.qualify_tables import qualify_tables


class SqlTouchPoints:
    def __init__(self):
        pass

    def extract(self, sql: str):
        ast = parse_one(sql, "snowflake")

        return self.walk(ast)

    def walk(self, node: exp.Node):
        match node:
            case exp.Select(select):
                pass




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
