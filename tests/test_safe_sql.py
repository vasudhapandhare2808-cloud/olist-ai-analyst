from src.safe_sql import run_safe_query


tests = {
    "valid SELECT": """
        SELECT COUNT(*) AS total_orders
        FROM olist_orders_dataset
    """,

    "DROP TABLE": """
        DROP TABLE olist_orders_dataset
    """,

    "DELETE": """
        DELETE FROM olist_orders_dataset
        WHERE order_status = 'canceled'
    """,

    "multiple statements": """
        SELECT COUNT(*) FROM olist_orders_dataset;
        DROP TABLE olist_orders_dataset;
    """,

    "COPY": """
        COPY olist_orders_dataset TO 'orders.csv'
    """,

    "empty query": "",
}


for name, query in tests.items():
    print(f"\nTEST: {name}")

    try:
        result = run_safe_query(query)
        print("PASS — allowed")
        print(result)

    except Exception as e:
        print("BLOCKED —", e)