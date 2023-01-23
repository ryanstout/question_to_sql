import collections
import math
import tiktoken


def token_entropy(text: str):
    enc = tiktoken.get_encoding("gpt2")
    encoded = enc.encode(text)

    return len(text) / float(len(encoded))


def estimate_shannon_entropy(dna_sequence):
    m = len(dna_sequence)
    bases = collections.Counter([tmp_base for tmp_base in dna_sequence])

    shannon_entropy_value = 0
    for base in bases:
        # number of residues
        n_i = bases[base]
        # n_i (# residues type i) / M (# residues in column)
        p_i = n_i / float(m)
        entropy_i = p_i * (math.log(p_i, 2))
        shannon_entropy_value += entropy_i

    return shannon_entropy_value * -1
