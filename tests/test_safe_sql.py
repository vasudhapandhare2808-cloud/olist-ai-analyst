
from src.safe_sql import run_safe_query


def test_valid_select():
    result = run_safe_query(
        """
        SELECT COUNT(*) AS total_orders
        FROM olist_orders_dataset
        """
    )

    assert result.iloc[0]["total_orders"] == 99441


def test_drop_table_blocked():
    try:
        run_safe_query("DROP TABLE olist_orders_dataset")
    except ValueError:
        return

    raise AssertionError("DROP TABLE should have been blocked.")


def test_delete_blocked():
    try:
        run_safe_query(
            """
            DELETE FROM olist_orders_dataset
            WHERE order_status = 'canceled'
            """
        )
    except ValueError:
        return

    raise AssertionError("DELETE should have been blocked.")


def test_multiple_statements_blocked():
    query = """
    SELECT COUNT(*) FROM olist_orders_dataset;
    DROP TABLE olist_orders_dataset;
    """

    try:
        run_safe_query(query)
    except ValueError:
        return

    raise AssertionError("Multiple SQL statements should have been blocked.")


def test_copy_blocked():
    try:
        run_safe_query(
            "COPY olist_orders_dataset TO 'orders.csv'"
        )
    except ValueError:
        return

    raise AssertionError("COPY should have been blocked.")


def test_empty_query_blocked():
    try:
        run_safe_query("")
    except ValueError:
        return

    raise AssertionError("An empty query should have been blocked.")


def test_database_still_intact():
    result = run_safe_query(
        "SELECT COUNT(*) AS total_orders FROM olist_orders_dataset"
    )

    assert result.iloc[0]["total_orders"] == 99441


if __name__ == "__main__":
    tests = [
        test_valid_select,
        test_drop_table_blocked,
        test_delete_blocked,
        test_multiple_statements_blocked,
        test_copy_blocked,
        test_empty_query_blocked,
        test_database_still_intact,
    ]

    for test in tests:
        test()
        print(f"PASS: {test.__name__}")

    print(f"\nALL {len(tests)} SAFE SQL TESTS PASSED")
