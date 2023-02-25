from typing import Tuple, TypeAlias

from python.sql.types import DbElementIds, ElementScores

ElementTrainingExamples: TypeAlias = list[Tuple[DbElementIds, ElementScores, int]]
