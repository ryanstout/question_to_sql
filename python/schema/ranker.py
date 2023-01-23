# Taking in the question, generate the following data structure to pass to
# the schema builder:
#
# {
#     'tableId1': {
#         'columnId1': ['valueHint1', 'valueHint2'],
#         'columnId2': [],
#         'columnId3': ['valueHint1', 'valueHint2', 'valueHint3'],
#     },
#     'tableId2': {
#         # ...
#     },
#     # ...
# }

class Ranker:
    def __init__(self, db):
