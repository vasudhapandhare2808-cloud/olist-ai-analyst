import duckdb
import sqlglot


DB_PATH = "olist.duckdb"


def validate_sql(sql):
    """Validate that the query contains exactly one SELECT statement."""

    if not sql or not sql.strip():
        raise ValueError("SQL query is empty.")

    try:
        statements = sqlglot.parse(sql, read="duckdb")
    except Exception as e:
        raise ValueError(f"Invalid SQL syntax: {e}")

    if len(statements) != 1:
        raise ValueError("Only one SQL statement is allowed.")

    statement = statements[0]

    if not isinstance(statement, sqlglot.exp.Select):
        raise ValueError("Only SELECT statements are allowed.")

    return True


def run_safe_query(sql):
    """Validate and execute a read-only analytical query."""

    validate_sql(sql)

    con = duckdb.connect(DB_PATH, read_only=True)

    try:
        result = con.execute(sql).fetchdf()
        return result
    finally:
        con.close()


if __name__ == "__main__":
    query = """
        SELECT
            order_status,
            COUNT(*) AS order_count
        FROM olist_orders_dataset
        GROUP BY order_status
        ORDER BY order_count DESC
    """

    result = run_safe_query(query)

    print(result)