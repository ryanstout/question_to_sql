
def normalize_fqn_quoting(fqn):
  names = fqn.split(".")
  names[-1] = f"\"{names[-1]}\""
  return ".".join(names)
