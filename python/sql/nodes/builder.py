from typing import Any, Dict, List

from sqlglot import exp

from python.sql.nodes.base import Base
from python.sql.nodes.column import Column
from python.sql.nodes.column_alias import ColumnAlias
from python.sql.nodes.eq import EQ
from python.sql.nodes.join import Join
from python.sql.nodes.select import Select
from python.sql.nodes.star import Star
from python.sql.nodes.subquery import Subquery
from python.sql.nodes.table import Table
from python.sql.types import SqlState


def new_state(previous_state: SqlState, new_state: Dict[str, Any]) -> SqlState:
    # Returns a new state dict with the new_state merged in
    state: SqlState = previous_state.copy()  # shallow clone
    state.update(new_state)  # type: ignore

    return state


def add_child(state: SqlState, add_to: List["Base"], start_node: exp.Expression) -> "Base":
    """Takes in a sqlglot expression node and returns a Base or child of
    Base instance to build our improved AST."""

    # Each branch shouuld set a `node` variable, that by default is resolved,
    # then appended to add_to, then returned. This can be overridden with a
    # return inside of the case.

    match start_node:
        case exp.Select() as select_expr:
            state = state.copy()
            node = Select(new_state(state, {"node": select_expr, "select": select_expr}))

            # The state should have the select point to itself
            state["select"] = node

            parse_select_args(state, node, select_expr.args)
        case exp.Table(args={"this": exp.Identifier(args={"this": table_name}), **rest}) as table_exp:
            # See if an alias is set
            alias_node = rest.get("alias")
            alias_name = alias_node.args.get("this").args.get("this") if alias_node else None

            node = Table(new_state(state, {"node": table_exp}), table_name, alias_name)
            add_children(state, node, table_exp.args)

        case exp.Column(args={"this": exp.Identifier(args={"this": column_name}), **rest}) as column_exp:
            # See if there's a table qualifier
            table_qualifier = rest.get("table")
            table_name = table_qualifier.args.get("this") if table_qualifier else None

            node = Column(new_state(state, {"node": column_exp}), column_name, table_name)
            add_children(state, node, column_exp.args)

        case exp.Alias(args={"alias": exp.Identifier(args={"this": alias_name}), **rest}) as alias_exp:
            table_qualifier = rest.get("table")
            if table_qualifier:
                del rest["table"]
                table_qualifier = table_qualifier.args["this"]

            node = ColumnAlias(new_state(state, {"node": alias_exp}), alias_name, table_qualifier)
            add_children(state, node, rest)

        case exp.Subquery(args={"this": exp.Expression() as select_exp, **rest}) as subquery_exp:
            alias_node = rest.get("alias")
            alias_name = alias_node.args.get("this").args.get("this") if alias_node else None

            node = Subquery(new_state(state, {"node": subquery_exp}), alias_name)
            add_children(state, node, {"select": select_exp})

        case exp.Join(
            args={
                "this": exp.Table() as join_table_exp,
                "kind": join_kind,
                "on": exp.Expression() as on_expression,
                **other,
            }
        ) as join_exp:
            if len(other) > 0:
                raise Exception(f"Unknown arg on join: {join_exp!r}")

            # Create a Base node to hold the join and the on
            join = Join(new_state(state, {"node": join_exp}))

            # Needs to be added before the "ON" can be evaluated
            add_to.append(join)
            add_children(state, join, {"joins": join_table_exp})

            # The on needs to be run after the joins have been added
            add_children(state, join, {"on": on_expression})

            # Join changes the append order, so we return it instead of letting
            # the default logic add it
            return join
        case exp.EQ(
            args={
                "this": exp.Expression() as column_exp,
                "expression": exp.Literal(args={"this": value_str, "is_string": True}),
            }
        ) as eq_exp:
            # Match on `column= 'value'` expressions
            node = EQ(state, value_str)
            add_children(state, node, {"column": column_exp})

        case exp.Column(args={"this": exp.Star() as star_exp, **rest}):
            # Qualified star shows up in a column
            table_alias = rest.get("table")
            table_alias = table_alias.args.get("this") if table_alias else None

            node = Star(state, table_alias)

        case exp.Star() as star_exp:
            node = Star(state, None)

        case exp.Expression() as expression:
            # Handle all other nodes, this combines the returned tables and
            # columns, which is useful for things like CONCAT, FIRST, MAX, etc..
            node = Base(new_state(state, {"node": expression}))
            add_children(state, node, expression.args)
        case _ as val:
            return val

    # The default flow is to resolve the node, then add it to its parent
    node.resolve()
    add_to.append(node)

    return node


def add_children(state: SqlState, node: "Base", exprs: Dict[str, exp.Expression] | List[exp.Expression]) -> None:
    """
    Build the subtree (child nodes) for the AST
    Child classes will override this to define the parse order (SELECT
    for example)
    """
    if isinstance(exprs, List):
        # A list of nodes was passed in
        for child in exprs:
            add_children(state, node, child.args)
        return

    # exp.Expression was passed in
    for key, child_or_list in exprs.items():
        nodes: List[Base] = []
        node.children[key] = nodes
        if isinstance(child_or_list, List):
            for child in child_or_list:
                add_child(state, nodes, child)
        else:
            add_child(state, nodes, child_or_list)


def parse_select_args(state: SqlState, node: "Base", expr: Dict[str, exp.Expression]):
    """
    The order we run the parts of the select matters for qualifying
    aliases. This recursively pulls parts off and then runs the rest.
    """
    match expr:
        case {"from": exp.From(args={"expressions": from_expressions}), **rest}:
            add_children(state, node, {"from": from_expressions})
            parse_select_args(state, node, rest)
        case {"joins": [*join_list], **rest}:
            # Add each join one by one
            add_children(state, node, {"join": join_list})
            parse_select_args(state, node, rest)
        case {"where": exp.Expression() as where_expression, **rest}:
            add_children(state, node, {"where": where_expression})
            parse_select_args(state, node, rest)
        case {"expressions": [exp.Expression()] as expressions, **rest}:
            add_children(state, node, {"expressions": expressions})
            parse_select_args(state, node, rest)
        case rest:
            add_children(state, node, rest)
