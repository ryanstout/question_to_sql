# Taking in the question, generate the following data structure to pass to
# the schema builder:
#
# {
#     'tableName1': {
#         'columnName1': ['valueHint1', 'valueHint2'],
#         'columnName2': [],
#         'columnName2': ['valueHint1', 'valueHint2', 'valueHint3'],
#     },
#     'tableName2': {
#         # ...
#     },
#     # ...
# }

class Ranker:
