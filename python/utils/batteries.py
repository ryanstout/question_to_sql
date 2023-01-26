# Collection of small helper functions that should be included in any language.. (Cough)


def unique(values):
    new_values = []
    for value in values:
        if value not in new_values:
            new_values.append(value)

    return new_values
