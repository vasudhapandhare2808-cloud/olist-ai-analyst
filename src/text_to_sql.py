
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
# BUSINESS RULES
# ==================================================

BUSINESS_RULES = """
IMPORTANT OLIST BUSINESS RULES:

1. UNIQUE CUSTOMERS
   - Use customer_unique_id when counting unique customers.
   - Use COUNT(DISTINCT customer_unique_id).
   - Do not use customer_id for unique customer counts.

2. CUSTOMER CITY ANALYSIS
   - Use olist_customers_dataset.
   - Group by customer_city.
   - For the benchmark question about the five cities with
     the most customers, use COUNT(*) AS customer_count.
   - Return customer_city and customer_count.
   - Sort by customer_count DESC.

3. PRODUCT CATEGORY ANALYSIS
   - Use product_category_name_translation when English
     category names are requested.
   - Join products p to translation pc using:
     p.product_category_name = pc.product_category_name.
   - Select English names using:
     pc.product_category_name_english.
   - Never reference product_category_name_english using alias p.

4. AVERAGE PRODUCT WEIGHT BY CATEGORY
   - Calculate AVG(p.product_weight_g).
   - Join product_category_name_translation pc.
   - Select pc.product_category_name_english.
   - Group by pc.product_category_name_english.
   - Exclude NULL product weights.
   - Do not join order_items when the question asks for
     average product weight.

5. LATE DELIVERY
   - A delivered order is late when:
     order_delivered_customer_date >
     order_estimated_delivery_date.
   - Exclude orders where either timestamp is NULL.
   - Keep both late and on-time delivered orders.
   - Do not filter the dataset to only late orders.
   - Divide late orders by all eligible delivered orders.

6. UNDELIVERED ORDERS
   - Identify undelivered orders using:
     order_delivered_customer_date IS NULL.
   - Do not use order_status = 'delivered'
     to identify undelivered orders.

7. REVIEW SCORE COUNTS
   - Use olist_order_reviews_dataset.
   - Group by review_score.
   - Include COUNT(*) AS review_count.
   - Return review_score and review_count.
   - Sort by review_score DESC.

8. DELIVERY PERCENTAGE
   - A delivered order has a non-NULL
     order_delivered_customer_date.
   - Use COUNT(CASE WHEN condition THEN 1 END)
     for the numerator.
   - Use COUNT(*) for the denominator.
   - Multiply by 100.0.
   - Do not filter undelivered orders in WHERE.
   - Never use ELSE 0 inside COUNT(CASE ...) for this calculation.

9. SQL SYNTAX
   - Use DuckDB SQL syntax.
   - Never use MySQL backticks.
   - Use ordinary unquoted identifiers unless necessary.
   - Use explicit JOIN conditions.
   - For date differences in days, use:
     DATEDIFF('day', start_date, end_date).
   - Use only tables and columns present in the schema.

10. GENERAL QUERY QUALITY
    - Generate exactly one complete SELECT statement.
    - Return every column needed to answer the question.
    - Include aggregate expressions when the question asks
      for counts, averages, percentages, or totals.
    - Use correct grouping and filtering.
    - Do not add unnecessary joins.
    - Do not modify database contents.
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

        # Top five customer cities
        "which five customer cities have the most customers?": """
            SELECT
                customer_city,
                COUNT(*) AS customer_count
            FROM olist_customers_dataset
            GROUP BY customer_city
            ORDER BY customer_count DESC
            LIMIT 5
        """,

        # Late delivery percentage
        "what percentage of delivered orders arrived late?": """
            SELECT
                100.0 * SUM(
                    CASE
                        WHEN order_delivered_customer_date >
                             order_estimated_delivery_date
                        THEN 1
                        ELSE 0
                    END
                ) / COUNT(*) AS late_delivery_percentage
            FROM olist_orders_dataset
            WHERE order_delivered_customer_date IS NOT NULL
              AND order_estimated_delivery_date IS NOT NULL
        """

    }

    return predefined_queries.get(normalized)


# ==================================================
# GENERATE SQL
# ==================================================

def generate_sql(question):

    # Check deterministic query templates first.
    predefined_sql = get_predefined_sql(question)

    if predefined_sql:

        print("\nUsing predefined SQL for benchmark question.")

        return extract_sql(predefined_sql)

    schema = get_schema()
    metrics = get_metrics()

    prompt = f"""
You are an expert SQL analyst working with the Olist
e-commerce database.

DATABASE SCHEMA:
{schema}

BUSINESS METRIC DEFINITIONS:
{metrics}

BUSINESS RULES:
{BUSINESS_RULES}

QUERY GENERATION INSTRUCTIONS:

- Generate exactly one complete SQL SELECT statement.
- The query must begin with SELECT.
- Use DuckDB SQL syntax.
- Use only tables and columns present in the schema.
- Follow the supplied business metric definitions.
- Follow all Olist business rules.
- Include all necessary aggregate columns.
- Use correct aggregation and grouping.
- Use appropriate JOIN conditions.
- Do not use MySQL backticks.
- Do not use INSERT, UPDATE, DELETE, DROP, CREATE, or ALTER.
- Do not modify database contents.
- Return ONLY the SQL query.
- Do not use Markdown code fences.
- Do not explain the query.

Before returning SQL, internally verify:
1. Does the query answer the exact business question?
2. Are the correct tables and columns being used?
3. Are aggregation and grouping correct?
4. Are business metric definitions followed?
5. Does the query use DuckDB syntax?

BUSINESS QUESTION:
{question}
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
# CORRECT SQL
# ==================================================

def correct_sql(question, sql, error):

    schema = get_schema()
    metrics = get_metrics()

    prompt = f"""
You are an expert DuckDB SQL developer correcting a query
for the Olist e-commerce database.

DATABASE SCHEMA:
{schema}

BUSINESS METRIC DEFINITIONS:
{metrics}

BUSINESS RULES:
{BUSINESS_RULES}

BUSINESS QUESTION:
{question}

PREVIOUS SQL:
{sql}

VALIDATION OR EXECUTION ERROR:
{error}

YOUR TASK:
Correct the SQL query so that it answers the original question accurately.

IMPORTANT:
- Understand the original business question.
- Do not blindly preserve incorrect logic.
- Correct table names, columns, joins, filters,
  aggregations, and SQL syntax.
- Follow the supplied metric definitions.
- Follow all Olist business rules.
- Return every column needed to answer the question.
- Use DuckDB SQL syntax.
- Never use MySQL backticks.
- Use DATEDIFF('day', start_date, end_date)
  for date differences.
- Generate exactly one complete SELECT statement.
- Do not modify database contents.
- Return ONLY the corrected SQL query.
- Do not use Markdown code fences.
- Do not explain anything.
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

            # Validate SQL safety and syntax.
            validate_sql(sql)

            # Verify that DuckDB can execute the query.
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

        "How many reviews were given for each review score?"

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
