import code
import sys
from sqlglot import diff, parse_one, exp
from sqlglot.optimizer import optimize

sql = sys.stdin.read()
# f = open("temp.sql", "r")
# sql = f.read()

ast = parse_one(sql)

def transformer(node):
    # print(type(node))
    if isinstance(node, exp.Div):
        # code.InteractiveConsole(locals=locals()).interact()
        # Need to cast one side on div's to float for postgres
        # Useful for "what percent" questions
        expr = node.args['this']

        if isinstance(node, exp.TableAlias):
            # Transform the contents of the AS node
            # code.InteractiveConsole(locals=locals()).interact()
            return node
        else:
            node.args['this'] = parse_one(f"{str(expr)}::float")
            return node
    return node

ast = ast.transform(transformer)

print(ast.sql(pretty=True, max_text_width=40))

# Drop into repl
# code.InteractiveConsole(locals=globals()).interact()