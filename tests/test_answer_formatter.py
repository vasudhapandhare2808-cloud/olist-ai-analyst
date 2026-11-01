
from src.answer_formatter import format_answer, format_value


def test_single_value():
    result = format_answer([{"count_star()": 99441}])

    assert result == "The result for count star() is 99,441."


def test_multiple_rows():
    rows = [
        {"category": "beauty", "item_count": 9670},
        {"category": "sports", "item_count": 8641},
    ]

    result = format_answer(rows)

    assert "beauty" in result
    assert "9,670" in result
    assert "sports" in result
    assert "8,641" in result


def test_empty_results():
    result = format_answer([])

    assert result == "The query returned no results."


def test_null_value():
    result = format_answer([{"average_score": None}])

    assert "Not available" in result


def test_float_precision():
    result = format_value(12.497336125)

    assert result == "12.497336125"


def test_integer_formatting():
    result = format_value(99441)

    assert result == "99,441"


def test_boolean_value():
    assert format_value(True) == "True"


def test_invalid_result():
    result = format_answer("invalid")

    assert result == "Invalid query result format."


if __name__ == "__main__":
    tests = [
        test_single_value,
        test_multiple_rows,
        test_empty_results,
        test_null_value,
        test_float_precision,
        test_integer_formatting,
        test_boolean_value,
        test_invalid_result,
    ]

    for test in tests:
        test()
        print(f"PASS: {test.__name__}")

    print("\nALL 8 ANSWER FORMATTER TESTS PASSED")
