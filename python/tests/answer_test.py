import unittest

import pytest


class TestAnswer(unittest.TestCase):
    def test_basic_answer(self):
        assert 42 == 42
