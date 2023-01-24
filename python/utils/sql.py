def unqualified_table_name(fqn: str) -> str:
    return fqn.split(".")[-1]


def normalize_fqn_quoting(fqn: str) -> str:
    names = fqn.split(".")
    names[-1] = f'"{names[-1]}"'
    return ".".join(names)
