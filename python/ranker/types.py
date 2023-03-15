import typing as t

DatasetPartitionType: t.TypeAlias = t.Literal["train", "test", "validation"]
DatasetElementType: t.TypeAlias = t.Literal["tables", "columns", "values"]
