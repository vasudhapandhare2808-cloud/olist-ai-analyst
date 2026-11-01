
from pathlib import Path

import duckdb
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "olist.duckdb"


def get_connection():
    """Create a read-only DuckDB connection."""
    return duckdb.connect(str(DB_PATH), read_only=True)


def fetch_df(query: str) -> pd.DataFrame:
    """Execute a dashboard query and return a DataFrame."""
    with get_connection() as con:
        return con.execute(query).fetchdf()


def get_kpis():
    """Return executive-level business KPIs."""

    query = """
    SELECT
        (SELECT COUNT(*) FROM olist_orders_dataset)
            AS total_orders,

        (SELECT COUNT(DISTINCT customer_unique_id)
         FROM olist_customers_dataset)
            AS total_customers,

        (SELECT ROUND(SUM(price), 2)
         FROM olist_order_items_dataset)
            AS product_sales,

        (SELECT ROUND(AVG(review_score), 2)
         FROM olist_order_reviews_dataset)
            AS average_review_score,

        (SELECT ROUND(
            100.0 * COUNT(
                CASE WHEN order_delivered_customer_date IS NOT NULL
                THEN 1 END
            ) / COUNT(*), 2
         )
         FROM olist_orders_dataset)
            AS delivery_rate,

        (SELECT ROUND(AVG(payment_value), 2)
         FROM olist_order_payments_dataset)
            AS average_payment_value
    """

    return fetch_df(query).iloc[0].to_dict()


def get_monthly_sales():
    """Monthly product sales and order volume."""

    return fetch_df("""
        SELECT
            DATE_TRUNC('month', o.order_purchase_timestamp) AS month,
            ROUND(SUM(i.price), 2) AS product_sales,
            COUNT(DISTINCT o.order_id) AS total_orders
        FROM olist_orders_dataset o
        JOIN olist_order_items_dataset i
            ON o.order_id = i.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY month
        ORDER BY month
    """)


def get_order_status():
    """Order distribution by status."""

    return fetch_df("""
        SELECT
            order_status,
            COUNT(*) AS order_count
        FROM olist_orders_dataset
        GROUP BY order_status
        ORDER BY order_count DESC
    """)


def get_top_categories(limit=10):
    """Top product categories by items sold."""

    return fetch_df(f"""
        SELECT
            COALESCE(
                t.product_category_name_english,
                'Untranslated / Unknown'
            ) AS category,
            COUNT(*) AS items_sold,
            ROUND(SUM(i.price), 2) AS product_sales
        FROM olist_order_items_dataset i
        JOIN olist_products_dataset p
            ON i.product_id = p.product_id
        LEFT JOIN product_category_name_translation t
            ON p.product_category_name = t.product_category_name
        GROUP BY category
        ORDER BY items_sold DESC
        LIMIT {int(limit)}
    """)


def get_customer_locations(limit=10):
    """Top customer cities."""

    return fetch_df(f"""
        SELECT
            customer_city,
            customer_state,
            COUNT(*) AS customer_count
        FROM olist_customers_dataset
        GROUP BY customer_city, customer_state
        ORDER BY customer_count DESC
        LIMIT {int(limit)}
    """)


def get_delivery_performance():
    """Delivery time and late delivery performance."""

    return fetch_df("""
        SELECT
            ROUND(
                AVG(
                    DATE_DIFF(
                        'day',
                        order_purchase_timestamp,
                        order_delivered_customer_date
                    )
                ), 2
            ) AS average_delivery_days,

            ROUND(
                100.0 * AVG(
                    CASE
                        WHEN order_delivered_customer_date >
                             order_estimated_delivery_date
                        THEN 1.0
                        ELSE 0.0
                    END
                ), 2
            ) AS late_delivery_percentage

        FROM olist_orders_dataset
        WHERE order_delivered_customer_date IS NOT NULL
          AND order_estimated_delivery_date IS NOT NULL
    """).iloc[0].to_dict()


def get_payment_types():
    """Payment distribution by payment method."""

    return fetch_df("""
        SELECT
            payment_type,
            COUNT(*) AS transaction_count,
            ROUND(SUM(payment_value), 2) AS total_payment
        FROM olist_order_payments_dataset
        GROUP BY payment_type
        ORDER BY total_payment DESC
    """)


def get_review_distribution():
    """Customer review score distribution."""

    return fetch_df("""
        SELECT
            review_score,
            COUNT(*) AS review_count
        FROM olist_order_reviews_dataset
        GROUP BY review_score
        ORDER BY review_score
    """)
