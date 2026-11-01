
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BENCHMARK_PATH = PROJECT_ROOT / "evaluation" / "benchmark.json"

NEW_QUESTIONS = [
    # ORDERS: 16-20
    {
        "id": 16,
        "category": "orders",
        "question": "How many orders were placed each month?",
        "expected_sql": """
            SELECT
                STRFTIME(order_purchase_timestamp, '%Y-%m') AS order_month,
                COUNT(*) AS order_count
            FROM olist_orders_dataset
            GROUP BY order_month
            ORDER BY order_month
        """,
        "expected_result": None
    },
    {
        "id": 17,
        "category": "orders",
        "question": "What is the average number of items per order?",
        "expected_sql": """
            SELECT AVG(item_count) AS average_items_per_order
            FROM (
                SELECT order_id, COUNT(*) AS item_count
                FROM olist_order_items_dataset
                GROUP BY order_id
            ) order_items
        """,
        "expected_result": None
    },
    {
        "id": 18,
        "category": "orders",
        "question": "What percentage of all orders were canceled?",
        "expected_sql": """
            SELECT ROUND(
                100.0 * COUNT(*) /
                (SELECT COUNT(*) FROM olist_orders_dataset), 2
            ) AS canceled_percentage
            FROM olist_orders_dataset
            WHERE order_status = 'canceled'
        """,
        "expected_result": None
    },
    {
        "id": 19,
        "category": "orders",
        "question": "How many orders were placed for each order status in each year?",
        "expected_sql": """
            SELECT
                YEAR(order_purchase_timestamp) AS order_year,
                order_status,
                COUNT(*) AS order_count
            FROM olist_orders_dataset
            GROUP BY order_year, order_status
            ORDER BY order_year, order_status
        """,
        "expected_result": None
    },
    {
        "id": 20,
        "category": "orders",
        "question": "Which ten customer states have the highest number of orders?",
        "expected_sql": """
            SELECT
                c.customer_state,
                COUNT(*) AS order_count
            FROM olist_orders_dataset o
            JOIN olist_customers_dataset c
                ON o.customer_id = c.customer_id
            GROUP BY c.customer_state
            ORDER BY order_count DESC
            LIMIT 10
        """,
        "expected_result": None
    },

    # CUSTOMERS: 21-24
    {
        "id": 21,
        "category": "customers",
        "question": "How many customers have placed more than one order?",
        "expected_sql": """
            SELECT COUNT(*) AS repeat_customers
            FROM (
                SELECT c.customer_unique_id
                FROM olist_orders_dataset o
                JOIN olist_customers_dataset c
                    ON o.customer_id = c.customer_id
                GROUP BY c.customer_unique_id
                HAVING COUNT(DISTINCT o.order_id) > 1
            ) repeat_customer_list
        """,
        "expected_result": None
    },
    {
        "id": 22,
        "category": "customers",
        "question": "What is the average number of orders per unique customer?",
        "expected_sql": """
            SELECT AVG(order_count) AS average_orders_per_customer
            FROM (
                SELECT
                    c.customer_unique_id,
                    COUNT(DISTINCT o.order_id) AS order_count
                FROM olist_customers_dataset c
                JOIN olist_orders_dataset o
                    ON c.customer_id = o.customer_id
                GROUP BY c.customer_unique_id
            ) customer_orders
        """,
        "expected_result": None
    },
    {
        "id": 23,
        "category": "customers",
        "question": "Which ten states have the most registered customer records?",
        "expected_sql": """
            SELECT
                customer_state,
                COUNT(*) AS customer_count
            FROM olist_customers_dataset
            GROUP BY customer_state
            ORDER BY customer_count DESC
            LIMIT 10
        """,
        "expected_result": None
    },
    {
        "id": 24,
        "category": "customers",
        "question": "How many unique customers are there in each state?",
        "expected_sql": """
            SELECT
                customer_state,
                COUNT(DISTINCT customer_unique_id) AS unique_customers
            FROM olist_customers_dataset
            GROUP BY customer_state
            ORDER BY unique_customers DESC
        """,
        "expected_result": None
    },

    # PRODUCTS: 25-27
    {
        "id": 25,
        "category": "products",
        "question": "How many products do not have a product category assigned?",
        "expected_sql": """
            SELECT COUNT(*) AS products_without_category
            FROM olist_products_dataset
            WHERE product_category_name IS NULL
        """,
        "expected_result": None
    },
    {
        "id": 26,
        "category": "products",
        "question": "Which ten product categories contain the most listed products?",
        "expected_sql": """
            SELECT
                t.product_category_name_english AS category,
                COUNT(DISTINCT p.product_id) AS product_count
            FROM olist_products_dataset p
            JOIN product_category_name_translation t
                ON p.product_category_name = t.product_category_name
            GROUP BY category
            ORDER BY product_count DESC
            LIMIT 10
        """,
        "expected_result": None
    },
    {
        "id": 27,
        "category": "products",
        "question": "What is the average selling price of items in each product category?",
        "expected_sql": """
            SELECT
                t.product_category_name_english AS category,
                ROUND(AVG(i.price), 2) AS average_item_price
            FROM olist_order_items_dataset i
            JOIN olist_products_dataset p
                ON i.product_id = p.product_id
            JOIN product_category_name_translation t
                ON p.product_category_name = t.product_category_name
            GROUP BY category
            ORDER BY average_item_price DESC
        """,
        "expected_result": None
    },

    # SALES AND REVENUE: 28-35
    {
        "id": 28,
        "category": "sales",
        "question": "What is the total revenue generated from product item prices?",
        "expected_sql": """
            SELECT ROUND(SUM(price), 2) AS total_product_revenue
            FROM olist_order_items_dataset
        """,
        "expected_result": None
    },
    {
        "id": 29,
        "category": "sales",
        "question": "What was the monthly product revenue from delivered orders?",
        "expected_sql": """
            SELECT
                STRFTIME(o.order_purchase_timestamp, '%Y-%m') AS order_month,
                ROUND(SUM(i.price), 2) AS monthly_revenue
            FROM olist_orders_dataset o
            JOIN olist_order_items_dataset i
                ON o.order_id = i.order_id
            WHERE o.order_status = 'delivered'
            GROUP BY order_month
            ORDER BY order_month
        """,
        "expected_result": None
    },
    {
        "id": 30,
        "category": "sales",
        "question": "Which ten product categories generated the highest product revenue?",
        "expected_sql": """
            SELECT
                t.product_category_name_english AS category,
                ROUND(SUM(i.price), 2) AS total_revenue
            FROM olist_order_items_dataset i
            JOIN olist_products_dataset p
                ON i.product_id = p.product_id
            JOIN product_category_name_translation t
                ON p.product_category_name = t.product_category_name
            GROUP BY category
            ORDER BY total_revenue DESC
            LIMIT 10
        """,
        "expected_result": None
    },
    {
        "id": 31,
        "category": "sales",
        "question": "What is the average product revenue per order?",
        "expected_sql": """
            SELECT ROUND(AVG(order_revenue), 2) AS average_order_value
            FROM (
                SELECT order_id, SUM(price) AS order_revenue
                FROM olist_order_items_dataset
                GROUP BY order_id
            ) order_totals
        """,
        "expected_result": None
    },
    {
        "id": 32,
        "category": "sales",
        "question": "Which ten sellers generated the highest product revenue?",
        "expected_sql": """
            SELECT
                i.seller_id,
                ROUND(SUM(i.price), 2) AS total_revenue
            FROM olist_order_items_dataset i
            GROUP BY i.seller_id
            ORDER BY total_revenue DESC
            LIMIT 10
        """,
        "expected_result": None
    },
    {
        "id": 33,
        "category": "sales",
        "question": "How much product revenue was generated in each year?",
        "expected_sql": """
            SELECT
                YEAR(o.order_purchase_timestamp) AS order_year,
                ROUND(SUM(i.price), 2) AS annual_revenue
            FROM olist_orders_dataset o
            JOIN olist_order_items_dataset i
                ON o.order_id = i.order_id
            GROUP BY order_year
            ORDER BY order_year
        """,
        "expected_result": None
    },
    {
        "id": 34,
        "category": "sales",
        "question": "What is the total payment value collected through each payment type?",
        "expected_sql": """
            SELECT
                payment_type,
                ROUND(SUM(payment_value), 2) AS total_payment_value
            FROM olist_order_payments_dataset
            GROUP BY payment_type
            ORDER BY total_payment_value DESC
        """,
        "expected_result": None
    },
    {
        "id": 35,
        "category": "sales",
        "question": "Which ten customer states generated the highest product revenue?",
        "expected_sql": """
            SELECT
                c.customer_state,
                ROUND(SUM(i.price), 2) AS total_revenue
            FROM olist_orders_dataset o
            JOIN olist_customers_dataset c
                ON o.customer_id = c.customer_id
            JOIN olist_order_items_dataset i
                ON o.order_id = i.order_id
            GROUP BY c.customer_state
            ORDER BY total_revenue DESC
            LIMIT 10
        """,
        "expected_result": None
    },

    # DELIVERY: 36-38
    {
        "id": 36,
        "category": "delivery",
        "question": "What is the average delivery time in days for each customer state?",
        "expected_sql": """
            SELECT
                c.customer_state,
                ROUND(
                    AVG(DATE_DIFF(
                        'day',
                        o.order_purchase_timestamp,
                        o.order_delivered_customer_date
                    )), 2
                ) AS average_delivery_days
            FROM olist_orders_dataset o
            JOIN olist_customers_dataset c
                ON o.customer_id = c.customer_id
            WHERE o.order_delivered_customer_date IS NOT NULL
            GROUP BY c.customer_state
            ORDER BY average_delivery_days
        """,
        "expected_result": None
    },
    {
        "id": 37,
        "category": "delivery",
        "question": "Which ten customer states have the highest late delivery rates?",
        "expected_sql": """
            SELECT
                c.customer_state,
                ROUND(
                    100.0 * SUM(
                        CASE
                            WHEN o.order_delivered_customer_date >
                                 o.order_estimated_delivery_date
                            THEN 1 ELSE 0
                        END
                    ) / COUNT(*), 2
                ) AS late_delivery_percentage
            FROM olist_orders_dataset o
            JOIN olist_customers_dataset c
                ON o.customer_id = c.customer_id
            WHERE o.order_delivered_customer_date IS NOT NULL
              AND o.order_estimated_delivery_date IS NOT NULL
            GROUP BY c.customer_state
            ORDER BY late_delivery_percentage DESC
            LIMIT 10
        """,
        "expected_result": None
    },
    {
        "id": 38,
        "category": "delivery",
        "question": "What is the average number of days that late orders exceeded their estimated delivery dates?",
        "expected_sql": """
            SELECT ROUND(
                AVG(DATE_DIFF(
                    'day',
                    order_estimated_delivery_date,
                    order_delivered_customer_date
                )), 2
            ) AS average_days_late
            FROM olist_orders_dataset
            WHERE order_delivered_customer_date IS NOT NULL
              AND order_estimated_delivery_date IS NOT NULL
              AND order_delivered_customer_date >
                  order_estimated_delivery_date
        """,
        "expected_result": None
    },

    # PAYMENTS: 39-40
    {
        "id": 39,
        "category": "payments",
        "question": "What is the average number of installments for each payment type?",
        "expected_sql": """
            SELECT
                payment_type,
                ROUND(AVG(payment_installments), 2) AS average_installments
            FROM olist_order_payments_dataset
            GROUP BY payment_type
            ORDER BY average_installments DESC
        """,
        "expected_result": None
    },
    {
        "id": 40,
        "category": "payments",
        "question": "How many payments were made in each installment count?",
        "expected_sql": """
            SELECT
                payment_installments,
                COUNT(*) AS payment_count
            FROM olist_order_payments_dataset
            GROUP BY payment_installments
            ORDER BY payment_installments
        """,
        "expected_result": None
    },

    # REVIEWS: 41-42
    {
        "id": 41,
        "category": "reviews",
        "question": "What is the average review score for each payment type?",
        "expected_sql": """
            SELECT
                p.payment_type,
                ROUND(AVG(r.review_score), 2) AS average_review_score
            FROM olist_order_reviews_dataset r
            JOIN olist_order_payments_dataset p
                ON r.order_id = p.order_id
            GROUP BY p.payment_type
            ORDER BY average_review_score DESC
        """,
        "expected_result": None
    },
    {
        "id": 42,
        "category": "reviews",
        "question": "What is the average review score for on-time and late delivered orders?",
        "expected_sql": """
            SELECT
                CASE
                    WHEN o.order_delivered_customer_date >
                         o.order_estimated_delivery_date
                    THEN 'late'
                    ELSE 'on_time'
                END AS delivery_status,
                ROUND(AVG(r.review_score), 2) AS average_review_score
            FROM olist_orders_dataset o
            JOIN olist_order_reviews_dataset r
                ON o.order_id = r.order_id
            WHERE o.order_delivered_customer_date IS NOT NULL
              AND o.order_estimated_delivery_date IS NOT NULL
            GROUP BY delivery_status
            ORDER BY delivery_status
        """,
        "expected_result": None
    },

    # COMPLEX JOINS: 43-45
    {
        "id": 43,
        "category": "complex_joins",
        "question": "What is the product revenue by customer state and product category?",
        "expected_sql": """
            SELECT
                c.customer_state,
                t.product_category_name_english AS category,
                ROUND(SUM(i.price), 2) AS total_revenue
            FROM olist_orders_dataset o
            JOIN olist_customers_dataset c
                ON o.customer_id = c.customer_id
            JOIN olist_order_items_dataset i
                ON o.order_id = i.order_id
            JOIN olist_products_dataset p
                ON i.product_id = p.product_id
            JOIN product_category_name_translation t
                ON p.product_category_name = t.product_category_name
            GROUP BY c.customer_state, category
            ORDER BY total_revenue DESC
            LIMIT 20
        """,
        "expected_result": None
    },
    {
        "id": 44,
        "category": "complex_joins",
        "question": "Which ten sellers have the highest number of distinct delivered orders?",
        "expected_sql": """
            SELECT
                i.seller_id,
                COUNT(DISTINCT o.order_id) AS delivered_order_count
            FROM olist_order_items_dataset i
            JOIN olist_orders_dataset o
                ON i.order_id = o.order_id
            WHERE o.order_status = 'delivered'
            GROUP BY i.seller_id
            ORDER BY delivered_order_count DESC
            LIMIT 10
        """,
        "expected_result": None
    },
    {
        "id": 45,
        "category": "complex_joins",
        "question": "What is the average review score by product category?",
        "expected_sql": """
            WITH order_category AS (
                SELECT DISTINCT
                    i.order_id,
                    t.product_category_name_english AS category
                FROM olist_order_items_dataset i
                JOIN olist_products_dataset p
                    ON i.product_id = p.product_id
                JOIN product_category_name_translation t
                    ON p.product_category_name = t.product_category_name
            )
            SELECT
                oc.category,
                ROUND(AVG(r.review_score), 2) AS average_review_score
            FROM order_category oc
            JOIN olist_order_reviews_dataset r
                ON oc.order_id = r.order_id
            GROUP BY oc.category
            ORDER BY average_review_score DESC
            LIMIT 10
        """,
        "expected_result": None
    }
]


def main():
    with BENCHMARK_PATH.open("r", encoding="utf-8") as file:
        benchmark = json.load(file)

    existing_ids = {case["id"] for case in benchmark}
    new_ids = [case["id"] for case in NEW_QUESTIONS]

    if len(existing_ids) != len(benchmark):
        raise ValueError("The existing benchmark contains duplicate IDs.")

    if existing_ids.intersection(new_ids):
        raise ValueError("Some new question IDs already exist.")

    if len(benchmark) != 15:
        raise ValueError(
            f"Expected 15 original questions, found {len(benchmark)}."
        )

    if len(NEW_QUESTIONS) != 30:
        raise ValueError("Expected exactly 30 new questions.")

    updated = benchmark + NEW_QUESTIONS

    with BENCHMARK_PATH.open("w", encoding="utf-8") as file:
        json.dump(updated, file, indent=4, ensure_ascii=False)

    print("Benchmark expanded successfully.")
    print(f"Original questions preserved: {len(benchmark)}")
    print(f"New questions added: {len(NEW_QUESTIONS)}")
    print(f"Total questions: {len(updated)}")


if __name__ == "__main__":
    main()
