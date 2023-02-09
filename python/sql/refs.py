from dataclasses import dataclass


@dataclass(init=False)
class TableRef:
    name: str

    def __init__(self, name: str):
        self.name = name


@dataclass(init=False)
class ColumnRef:
    name: str
    table: TableRef

    def __init__(self, name: str, table: TableRef):
        self.name = name
        self.table = table
