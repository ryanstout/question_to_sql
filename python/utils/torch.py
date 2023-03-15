import torch.backends.mps


def device_type():
    is_mps = torch.backends.mps.is_available() and torch.backends.mps.is_built()

    return "mps" if is_mps else "cpu"
