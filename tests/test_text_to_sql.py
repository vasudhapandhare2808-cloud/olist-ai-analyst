from src.text_to_sql import generate_valid_sql
from src.safe_sql import run_safe_query


TEST_CASES = [
    {
        "question": "How many orders were delivered?",
        "expected": 96478,
        "tolerance": 0,
        "metric": "delivered_orders",
    },
    {
        "question": "What is the average delivery time in days?",
        "expected": 12.497336125046644,
        "tolerance": 0.01,
        "metric": "average_delivery_time",
    },
    {
        "question": "What is the average review score?",
        "expected": 4.08642062404257,
        "tolerance": 0.01,
        "metric": "average_review_score",
    },
    {
        "question": "How many total orders are in the dataset?",
        "expected": 99441,
        "tolerance": 0,
        "metric": "total_orders",
    },
    {
        "question": "How many customers are in the dataset?",
        "expected": 99441,
        "tolerance": 0,
        "metric": "total_customers",
    },
    {
        "question": "How many sellers are in the dataset?",
        "expected": 3095,
        "tolerance": 0,
        "metric": "total_sellers",
    },
    {
        "question": "What is the average payment value?",
        "expected": 154.10038041698365,
        "tolerance": 0.01,
        "metric": "average_payment_value",
    },
    {
        "question": "What are the top 5 product categories by number of items sold?",
        "expected": [
            ["bed_bath_table", 11115],
            ["health_beauty", 9670],
            ["sports_leisure", 8641],
            ["furniture_decor", 8334],
            ["computers_accessories", 7827],
        ],
        "tolerance": 0,
        "metric": "top_5_categories_by_items",
    },
    {
        "question": "What percentage of delivered orders were delivered late?",
        "expected": 8.11,
        "tolerance": 0.01,
        "metric": "late_delivery_rate",
    },
    {
        "question": "What is the most common order status?",
        "expected": "delivered",
        "tolerance": 0,
        "metric": "most_common_order_status",
    },
]


def values_match(actual, expected, tolerance):
    """
    Compare numeric, text, and list results.
    """

    # Numeric result
    if isinstance(expected, (int, float)):
        try:
            return abs(float(actual) - float(expected)) <= tolerance
        except (TypeError, ValueError):
            return False

    # Text result
    if isinstance(expected, str):
        return str(actual).strip().lower() == expected.strip().lower()

    # List / ranked result
    if isinstance(expected, list):
        return actual == expected

    return actual == expected


def run_test(case):
    print("\n" + "=" * 60)

    print("Question:")
    print(case["question"])

    print("\nMetric:")
    print(case["metric"])

    try:
        # Generate SQL with self-correction
        sql = generate_valid_sql(case["question"])

        print("\nGenerated SQL:")
        print(sql)

        # Execute safely
        result = run_safe_query(sql)

        # Convert result into a comparable Python value
        if result.shape[0] == 1 and result.shape[1] == 1:
            actual = result.iloc[0, 0]
        else:
            actual = result.values.tolist()

        expected = case["expected"]
        tolerance = case["tolerance"]

        passed = values_match(actual, expected, tolerance)

        print("\nExpected:")
        print(expected)

        print("\nActual:")
        print(actual)

        print("\nStatus:")
        print("PASS" if passed else "FAIL")

        return passed

    except Exception as e:
        print("\nStatus:")
        print("ERROR")

        print("\nError:")
        print(e)

        return False


if __name__ == "__main__":

    results = []

    for case in TEST_CASES:
        results.append(run_test(case))

    print("\n" + "=" * 60)

    passed_count = sum(results)
    total_count = len(results)

    print(f"Passed: {passed_count}/{total_count}")

    if all(results):
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")