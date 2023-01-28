import unittest

import pytest


class TestSchemaBuilder(unittest.TestCase):
    def test_id_inclusion(self):
        ranking = [
            {"table_id": 1, "column_id": 1, "value_hint": "best-selling", "score": 0.8065115213394165},
        ]
