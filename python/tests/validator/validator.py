from python.validation.validator import check_match


def test_check_match_column_order_invariance():
    results_a = [
        {"a": 1, "b": 2},
        {"a": 3, "b": 4},
        {"a": 5, "b": 6},
    ]
    results_b = [
        {"b": 2, "a": 1},
        {"a": 3, "b": 4},
        {"b": 6, "a": 5},
    ]

    assert check_match(results_a, results_b) is True
