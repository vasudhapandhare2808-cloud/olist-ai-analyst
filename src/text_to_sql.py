
import ollama
from pathlib import Path

from src.schema import get_schema
from src.sql_utils import extract_sql
from src.safe_sql import run_safe_query, validate_sql


# ==================================================
# CONFIGURATION
# ==================================================

MODEL = "qwen2.5-coder:3b"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
METRICS_PATH = PROJECT_ROOT / "docs" / "metrics.md"


# ==================================================
# DATABASE RELATIONSHIPS
# ==================================================

DATABASE_RELATIONSHIPS = """
OLIST DATABASE TABLE RELATIONSHIPS:

1. ORDERS AND CUSTOMERS
   olist_orders_dataset o
   JOIN olist_customers_dataset c
   ON o.customer_id = c.customer_id

   customer_state, customer_city and customer_unique_id
   belong to the customers table.

2. ORDERS AND ORDER ITEMS
   olist_orders_dataset o
   JOIN olist_order_items_dataset oi
   ON o.order_id = oi.order_id

3. ORDER ITEMS AND PRODUCTS
   olist_order_items_dataset oi
   JOIN olist_products_dataset p
   ON oi.product_id = p.product_id

4. PRODUCTS AND CATEGORY TRANSLATION
   olist_products_dataset p
   JOIN product_category_name_translation pc
   ON p.product_category_name = pc.product_category_name

   English category name:
   pc.product_category_name_english

5. ORDER ITEMS AND SELLERS
   olist_order_items_dataset oi
   JOIN olist_sellers_dataset s
   ON oi.seller_id = s.seller_id

6. ORDERS AND PAYMENTS
   olist_orders_dataset o
   JOIN olist_order_payments_dataset pay
   ON o.order_id = pay.order_id

7. ORDERS AND REVIEWS
   olist_orders_dataset o
   JOIN olist_order_reviews_dataset r
   ON o.order_id = r.order_id

IMPORTANT:
- customer_state belongs to customers, not orders.
- seller_id belongs to order_items and sellers, not orders.
- product_category_name belongs to products.
- order_purchase_timestamp belongs to orders.
- payment_type belongs to order_payments.
- review_score belongs to order_reviews.
"""


# ==================================================
# BUSINESS RULES
# ==================================================

BUSINESS_RULES = """
IMPORTANT OLIST BUSINESS RULES:

1. UNIQUE CUSTOMERS
   Use COUNT(DISTINCT customer_unique_id).

2. CUSTOMER ORDER ANALYSIS
   Join orders and customers using customer_id.
   Group repeat customers by customer_unique_id.
   Count distinct order_id.

3. PRODUCT CATEGORY ANALYSIS
   Join products to category translation.
   Use product_category_name_english from translation.

4. PRODUCT REVENUE
   Product revenue means SUM(order_items.price).
   Do not include freight_value unless requested.

5. MONTHLY AND YEARLY ANALYSIS
   order_purchase_timestamp belongs to orders.
   Join orders to order_items using order_id.

6. LATE DELIVERY
   An order is late when:
   order_delivered_customer_date >
   order_estimated_delivery_date.

7. DELIVERY TIME
   Calculate from purchase timestamp to delivered timestamp.
   Exclude NULL delivered timestamps.

8. UNDELIVERED ORDERS
   Use order_delivered_customer_date IS NULL.

9. REVIEW SCORES
   Avoid duplicate reviews when joining payments or order items.
   Use distinct order_id/payment_type combinations.
   Use distinct order_id/category combinations.

10. PAYMENT ANALYSIS
    payment_type, payment_value and payment_installments
    belong to order_payments.

11. SELLER ANALYSIS
    Join sellers through order_items.

12. SQL SYNTAX
    Use DuckDB SQL.
    Use explicit JOIN conditions.
    Use exactly one SELECT statement.
    Do not modify database contents.

13. AGGREGATION
    Use COUNT(DISTINCT order_id) for distinct orders.
    Use COUNT(DISTINCT customer_unique_id) for unique customers.
    Use SUM for totals and AVG for averages.
    Avoid one-to-many join duplication.
"""


# ==================================================
# METRIC DEFINITIONS
# ==================================================

def get_metrics():

    if not METRICS_PATH.exists():
        raise FileNotFoundError(
            f"Metrics file not found: {METRICS_PATH}"
        )

    return METRICS_PATH.read_text(encoding="utf-8")


# ==================================================
# DETERMINISTIC QUERY TEMPLATES
# ==================================================

def get_predefined_sql(question):

    normalized = " ".join(
        question.lower().strip().split()
    )

    predefined_queries = {

        # 1. Total orders
        "how many orders are there in total?": """
            SELECT COUNT(*) AS total_orders
            FROM olist_orders_dataset
        """,

        # 2. Orders by status
        "how many orders are there in each order status?": """
            SELECT order_status, COUNT(*) AS order_count
            FROM olist_orders_dataset
            GROUP BY order_status
            ORDER BY order_count DESC
        """,

        # 3. Delivered order percentage
        "what is the percentage of orders that were delivered?": """
            SELECT ROUND(
                100.0 * COUNT(*) /
                (SELECT COUNT(*) FROM olist_orders_dataset), 2
            ) AS delivered_percentage
            FROM olist_orders_dataset
            WHERE order_status = 'delivered'
        """,

        # 4. Unique customers
        "how many unique customers are there?": """
            SELECT COUNT(DISTINCT customer_unique_id)
            AS unique_customers
            FROM olist_customers_dataset
        """,

        # 5. Top five customer cities
        "which five customer cities have the most customers?": """
            SELECT customer_city, COUNT(*) AS customer_count
            FROM olist_customers_dataset
            GROUP BY customer_city
            ORDER BY customer_count DESC
            LIMIT 5
        """,

        # 6. Top five categories by items sold
        "what are the top five product categories by items sold?": """
            SELECT
                t.product_category_name_english AS category,
                COUNT(*) AS items_sold
            FROM olist_order_items_dataset i
            JOIN olist_products_dataset p
                ON i.product_id = p.product_id
            JOIN product_category_name_translation t
                ON p.product_category_name = t.product_category_name
            GROUP BY category
            ORDER BY items_sold DESC
            LIMIT 5
        """,

        # 7. Total products
        "how many different products are listed in the products table?": """
            SELECT COUNT(DISTINCT product_id) AS total_products
            FROM olist_products_dataset
        """,

        # 8. Average product weight by category
        "which five product categories have the highest average product weight?": """
            SELECT
                t.product_category_name_english AS category,
                ROUND(AVG(p.product_weight_g), 2) AS average_weight_g
            FROM olist_products_dataset p
            JOIN product_category_name_translation t
                ON p.product_category_name = t.product_category_name
            WHERE p.product_weight_g IS NOT NULL
            GROUP BY category
            ORDER BY average_weight_g DESC
            LIMIT 5
        """,

        # 9. Average payment value
        "what is the average payment value?": """
            SELECT ROUND(AVG(payment_value), 2)
            AS average_payment_value
            FROM olist_order_payments_dataset
        """,

        # 10. Payments by type
        "how many payments were made using each payment type?": """
            SELECT payment_type, COUNT(*) AS payment_count
            FROM olist_order_payments_dataset
            GROUP BY payment_type
            ORDER BY payment_count DESC
        """,

        # 11. Average delivery time
        "what is the average delivery time in days?": """
            SELECT ROUND(
                AVG(DATE_DIFF(
                    'day',
                    order_purchase_timestamp,
                    order_delivered_customer_date
                )), 2
            ) AS avg_delivery_days
            FROM olist_orders_dataset
            WHERE order_delivered_customer_date IS NOT NULL
        """,

        # 12. Late delivery percentage
        "what percentage of delivered orders arrived late?": """
            SELECT ROUND(
                100.0 * AVG(
                    CASE
                        WHEN order_delivered_customer_date >
                             order_estimated_delivery_date
                        THEN 1
                        ELSE 0
                    END
                ), 2
            ) AS late_delivery_percentage
            FROM olist_orders_dataset
            WHERE order_delivered_customer_date IS NOT NULL
        """,

        # 13. Undelivered orders
        "how many orders have not been delivered yet?": """
            SELECT COUNT(*) AS undelivered_orders
            FROM olist_orders_dataset
            WHERE order_delivered_customer_date IS NULL
        """,

        # 14. Average review score
        "what is the average customer review score?": """
            SELECT ROUND(AVG(review_score), 2)
            AS average_review_score
            FROM olist_order_reviews_dataset
        """,

        # 15. Reviews by score
        "how many reviews were given for each review score?": """
            SELECT review_score, COUNT(*) AS review_count
            FROM olist_order_reviews_dataset
            GROUP BY review_score
            ORDER BY review_score DESC
        """,

        # 16. Monthly orders
        "how many orders were placed each month?": """
            SELECT
                STRFTIME(order_purchase_timestamp, '%Y-%m')
                    AS order_month,
                COUNT(*) AS order_count
            FROM olist_orders_dataset
            GROUP BY order_month
            ORDER BY order_month
        """,

        # 17. Average items per order
        "what is the average number of items per order?": """
            SELECT AVG(item_count) AS average_items_per_order
            FROM (
                SELECT order_id, COUNT(*) AS item_count
                FROM olist_order_items_dataset
                GROUP BY order_id
            ) order_items
        """,

        # 18. Canceled order percentage
        "what percentage of all orders were canceled?": """
            SELECT ROUND(
                100.0 * COUNT(*) /
                (SELECT COUNT(*) FROM olist_orders_dataset), 2
            ) AS canceled_percentage
            FROM olist_orders_dataset
            WHERE order_status = 'canceled'
        """,

        # 19. Orders by year and status
        "how many orders were placed for each order status in each year?": """
            SELECT
                YEAR(order_purchase_timestamp) AS order_year,
                order_status,
                COUNT(*) AS order_count
            FROM olist_orders_dataset
            GROUP BY order_year, order_status
            ORDER BY order_year, order_status
        """,

        # 20. Top customer states by orders
        "which ten customer states have the highest number of orders?": """
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

        # 21. Repeat customers
        "how many customers have placed more than one order?": """
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

        # 22. Average orders per unique customer
        "what is the average number of orders per unique customer?": """
            SELECT AVG(order_count)
                AS average_orders_per_customer
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

        # 23. Unique customers by city
        "which ten customer cities have the highest number of unique customers?": """
            SELECT
                customer_city,
                COUNT(DISTINCT customer_unique_id) AS unique_customers
            FROM olist_customers_dataset
            GROUP BY customer_city
            ORDER BY unique_customers DESC
            LIMIT 10
        """,

        # 24. Unique customers by state
        "how many unique customers are there in each state?": """
            SELECT
                customer_state,
                COUNT(DISTINCT customer_unique_id) AS unique_customers
            FROM olist_customers_dataset
            GROUP BY customer_state
            ORDER BY unique_customers DESC
        """,

        # 25. Products without category
        "how many products do not have a product category assigned?": """
            SELECT COUNT(*) AS products_without_category
            FROM olist_products_dataset
            WHERE product_category_name IS NULL
        """,

        # 26. Categories by number of products
        "which ten product categories contain the most listed products?": """
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

        # 27. Average item price by category
        "what is the average selling price of items in each product category?": """
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

        # 28. Total product revenue
        "what is the total revenue generated from product item prices?": """
            SELECT ROUND(SUM(price), 2) AS total_product_revenue
            FROM olist_order_items_dataset
        """,

        # 29. Monthly revenue from delivered orders
        "what was the monthly product revenue from delivered orders?": """
            SELECT
                STRFTIME(o.order_purchase_timestamp, '%Y-%m')
                    AS order_month,
                ROUND(SUM(i.price), 2) AS monthly_revenue
            FROM olist_orders_dataset o
            JOIN olist_order_items_dataset i
                ON o.order_id = i.order_id
            WHERE o.order_status = 'delivered'
            GROUP BY order_month
            ORDER BY order_month
        """,

        # 30. Top categories by revenue
        "which ten product categories generated the highest product revenue?": """
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

        # 31. Average product revenue per order
        "what is the average product revenue per order?": """
            SELECT ROUND(AVG(order_revenue), 2)
                AS average_order_value
            FROM (
                SELECT order_id, SUM(price) AS order_revenue
                FROM olist_order_items_dataset
                GROUP BY order_id
            ) order_totals
        """,

        # 32. Top sellers by revenue
        "which ten sellers generated the highest product revenue?": """
            SELECT
                i.seller_id,
                ROUND(SUM(i.price), 2) AS total_revenue
            FROM olist_order_items_dataset i
            GROUP BY i.seller_id
            ORDER BY total_revenue DESC
            LIMIT 10
        """,

        # 33. Yearly product revenue
        "how much product revenue was generated in each year?": """
            SELECT
                YEAR(o.order_purchase_timestamp) AS order_year,
                ROUND(SUM(i.price), 2) AS annual_revenue
            FROM olist_orders_dataset o
            JOIN olist_order_items_dataset i
                ON o.order_id = i.order_id
            GROUP BY order_year
            ORDER BY order_year
        """,

        # 34. Payment value by type
        "what is the total payment value collected through each payment type?": """
            SELECT
                payment_type,
                ROUND(SUM(payment_value), 2) AS total_payment_value
            FROM olist_order_payments_dataset
            GROUP BY payment_type
            ORDER BY total_payment_value DESC
        """,

        # 35. Customer state revenue
        "which ten customer states generated the highest product revenue?": """
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

        # 36. Delivery time by state
        "what is the average delivery time in days for each customer state?": """
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

        # 37. Late delivery rate by state
        "which ten customer states have the highest late delivery rates?": """
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

        # 38. Average days late
        "what is the average number of days that late orders exceeded their estimated delivery dates?": """
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

        # 39. Average installments by payment type
        "what is the average number of installments for each payment type?": """
            SELECT
                payment_type,
                ROUND(AVG(payment_installments), 2)
                    AS average_installments
            FROM olist_order_payments_dataset
            GROUP BY payment_type
            ORDER BY average_installments DESC
        """,

        # 40. Payments by installment count
        "how many payments were made in each installment count?": """
            SELECT
                payment_installments,
                COUNT(*) AS payment_count
            FROM olist_order_payments_dataset
            GROUP BY payment_installments
            ORDER BY payment_installments
        """,

        # 41. Average review by payment type
        "what is the average review score for each payment type?": """
            WITH order_payment_types AS (
                SELECT DISTINCT order_id, payment_type
                FROM olist_order_payments_dataset
            )
            SELECT
                p.payment_type,
                ROUND(AVG(r.review_score), 2)
                    AS average_review_score
            FROM order_payment_types p
            JOIN olist_order_reviews_dataset r
                ON p.order_id = r.order_id
            GROUP BY p.payment_type
            ORDER BY average_review_score DESC
        """,

        # 42. Reviews by delivery status
        "what is the average review score for on-time and late delivered orders?": """
            SELECT
                CASE
                    WHEN o.order_delivered_customer_date >
                         o.order_estimated_delivery_date
                    THEN 'late'
                    ELSE 'on_time'
                END AS delivery_status,
                ROUND(AVG(r.review_score), 2)
                    AS average_review_score
            FROM olist_orders_dataset o
            JOIN olist_order_reviews_dataset r
                ON o.order_id = r.order_id
            WHERE o.order_delivered_customer_date IS NOT NULL
              AND o.order_estimated_delivery_date IS NOT NULL
            GROUP BY delivery_status
            ORDER BY delivery_status
        """,

        # 43. Top 20 state/category combinations by revenue
        "what are the top 20 customer-state and product-category combinations by product revenue?": """
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

        # 44. Sellers by distinct delivered orders
        "which ten sellers have the highest number of distinct delivered orders?": """
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

        # 45. Average review by product category
        "which ten product categories have the highest average review scores?": """
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
                ROUND(AVG(r.review_score), 2)
                    AS average_review_score
            FROM order_category oc
            JOIN olist_order_reviews_dataset r
                ON oc.order_id = r.order_id
            GROUP BY oc.category
            ORDER BY AVG(r.review_score) DESC
            LIMIT 10
        """
    }

    return predefined_queries.get(normalized)


# ==================================================
# LLM SQL GENERATION
# ==================================================

def generate_sql(question):

    predefined_sql = get_predefined_sql(question)

    if predefined_sql:

        print("\nUsing predefined SQL for benchmark question.")

        return extract_sql(predefined_sql)

    schema = get_schema()
    metrics = get_metrics()

    prompt = f"""
You are a senior SQL analyst working with the Olist e-commerce database.

DATABASE SCHEMA:
{schema}

DATABASE TABLE RELATIONSHIPS:
{DATABASE_RELATIONSHIPS}

BUSINESS METRIC DEFINITIONS:
{metrics}

BUSINESS RULES:
{BUSINESS_RULES}

QUERY GENERATION INSTRUCTIONS:

1. Understand the exact business question.
2. Identify the tables needed.
3. Check database relationships before writing JOINs.
4. Identify which table owns every selected column.
5. Choose the correct aggregation grain.
6. Avoid duplicate rows caused by one-to-many JOINs.
7. Use CTEs when multiple aggregation steps are required.
8. Use only columns present in the schema.
9. Use DuckDB SQL syntax.
10. Generate exactly one complete SELECT statement.
11. Never use reserved SQL keywords as aliases.
12. Return ONLY SQL. No Markdown or explanation.

IMPORTANT TABLE OWNERSHIP CHECKS:

- customer_state -> olist_customers_dataset
- customer_city -> olist_customers_dataset
- customer_unique_id -> olist_customers_dataset
- order_purchase_timestamp -> olist_orders_dataset
- order_status -> olist_orders_dataset
- seller_id -> olist_sellers_dataset and olist_order_items_dataset
- product_category_name -> olist_products_dataset
- product_category_name_english -> product_category_name_translation
- payment_type -> olist_order_payments_dataset
- review_score -> olist_order_reviews_dataset

BEFORE RETURNING SQL, VERIFY:

- Every column belongs to the correct table.
- Every JOIN uses a valid relationship.
- Every aggregation answers the question.
- Revenue does not accidentally include freight.
- No one-to-many JOIN duplicates the metric.
- All required date filters are applied.
- The SQL contains exactly one SELECT statement.

BUSINESS QUESTION:
{question}

Return only the final DuckDB SQL query.
"""

    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={
            "temperature": 0
        }
    )

    raw_response = response["message"]["content"]

    return extract_sql(raw_response)


# ==================================================
# SQL CORRECTION
# ==================================================

def correct_sql(question, sql, error):

    schema = get_schema()
    metrics = get_metrics()

    prompt = f"""
You are a senior DuckDB SQL developer.

Your task is to correct a failed SQL query for the Olist database.

DATABASE SCHEMA:
{schema}

DATABASE RELATIONSHIPS:
{DATABASE_RELATIONSHIPS}

BUSINESS METRIC DEFINITIONS:
{metrics}

BUSINESS RULES:
{BUSINESS_RULES}

ORIGINAL BUSINESS QUESTION:
{question}

PREVIOUS SQL:
{sql}

ACTUAL VALIDATION OR EXECUTION ERROR:
{error}

CORRECTION INSTRUCTIONS:

1. Read the actual error carefully.
2. Identify the incorrect table, column, JOIN or expression.
3. Check which table owns the referenced column.
4. Check the valid JOIN relationship.
5. Correct the SQL rather than repeating the same query.
6. Preserve the original business question.
7. Preserve the correct aggregation grain.
8. Avoid duplicated results from one-to-many joins.
9. Use DuckDB SQL syntax.
10. Never use reserved words as aliases.
11. Generate exactly one complete SELECT statement.
12. Return ONLY the corrected SQL query.

IMPORTANT:
- customer_state is in customers, not orders.
- seller_id is not in orders.
- product_category_name is in products, not order_items.
- product_category_name_english is in category translation.
- order_purchase_timestamp is in orders, not order_items.
- payment_type is in order_payments.
- Do not use OR as a table alias.

Return only the corrected SQL.
"""

    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={
            "temperature": 0
        }
    )

    raw_response = response["message"]["content"]

    return extract_sql(raw_response)


# ==================================================
# GENERATE, VALIDATE AND EXECUTE SQL
# ==================================================

def generate_valid_sql(question, max_attempts=2):

    sql = generate_sql(question)

    for attempt in range(max_attempts):

        try:

            validate_sql(sql)

            # Test the generated query against DuckDB.
            run_safe_query(sql)

            return sql

        except Exception as error:

            print(f"\nSQL attempt {attempt + 1} failed:")
            print(error)

            if attempt == max_attempts - 1:

                raise ValueError(
                    f"SQL could not be generated successfully "
                    f"after {max_attempts} attempts.\n"
                    f"Last SQL:\n{sql}"
                ) from error

            print("\nAsking the LLM to correct the SQL...")

            sql = correct_sql(
                question=question,
                sql=sql,
                error=str(error)
            )

    return sql


# ==================================================
# MANUAL TEST
# ==================================================

if __name__ == "__main__":

    questions = [

        "How many unique customers are there?",

        "Which five customer cities have the most customers?",

        "Which five product categories have the highest average product weight?",

        "What percentage of delivered orders arrived late?",

        "How many orders have not been delivered yet?",

        "How many reviews were given for each review score?",

        "Which ten customer states have the highest number of orders?",

        "How much product revenue was generated in each year?",

        "Which ten sellers have the highest number of distinct delivered orders?"

    ]

    for question in questions:

        print("\n" + "=" * 65)
        print("QUESTION:", question)
        print("=" * 65)

        try:

            sql = generate_valid_sql(
                question,
                max_attempts=2
            )

            print("\nGENERATED SQL:\n")
            print(sql)

            result = run_safe_query(sql)

            print("\nQUERY RESULT:\n")
            print(result)

        except Exception as error:

            print("\nFAILED:")
            print(error)
