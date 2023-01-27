# Embedding Links point from a faiss search result index to a table_id,
# column_id and value string for the SchemaBuilder

import numpy as np

from python.utils.logging import log


class EmbeddingLinkIndex:
    def __init__(self, path):
        self.path = path
        self.rows = []

    def add(self, index: int, table_id: int, column_id: int, value: str):
        self.rows.append([index, table_id, column_id, value])

    def load(self):
        # Load the index from disk memory mapped
        self.table_and_columns = np.load(self.path + ".table_cols.npy", mmap_mode="r")
        self.values = np.load(self.path + ".values.npy", allow_pickle=True)

    def save(self):
        # Find the max index in rows
        max_index = max(self.rows, key=lambda x: x[0])[0]

        log.debug("Save EmbeddingLink index", size=max_index)

        # Create the numpy arrays for the table_id/column_id and the value
        # strings
        self.table_and_columns = np.zeros((max_index + 1, 2), dtype=np.int32)
        self.values = np.empty(max_index + 1, dtype=object)

        # Loop through the rows and assign each now that we know the number
        # of rows.
        for idx, row in enumerate(self.rows):
            # Assign -1 for None valuese
            self.table_and_columns[idx, 0] = row[1] or -1
            self.table_and_columns[idx, 1] = row[2] or -1
            self.values[idx] = row[3] or ""

        # Seralize index to disk, just use .np format, not npz so we can jump
        # directly to the spot in memory
        np.save(self.path + ".table_cols", self.table_and_columns)
        np.save(self.path + ".values", self.values)

    def query(self, index: int):
        table_id = self.table_and_columns[index, 0].item()
        column_id = self.table_and_columns[index, 1].item()
        value = self.values[index]

        if table_id == -1:
            table_id = None

        if column_id == -1:
            column_id = None

        if value == "":
            value = None

        return [table_id, column_id, value]