import pandas as pd

from src.result_validator import validate_result


def test_valid_result():
    result = pd.DataFrame({
        "value": [10]
    })

    assert validate_result(result) is True


def test_empty_result():
    result = pd.DataFrame()

    try:
        validate_result(result)
        assert False
    except ValueError as e:
        assert str(e) == "Query returned no rows."


def test_null_result():
    result = pd.DataFrame({
        "value": [None]
    })

    try:
        validate_result(result)
        assert False
    except ValueError as e:
        assert str(e) == "Query result contains NULL values."


if __name__ == "__main__":
    test_valid_result()
    test_empty_result()
    test_null_result()
    print("ALL RESULT VALIDATION TESTS PASSED")