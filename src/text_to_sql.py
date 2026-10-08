import ollama
from src.schema import get_schema
from src.sql_utils import extract_sql
from src.safe_sql import run_safe_query, validate_sql
from pathlib import Path
from src.result_validator import validate_result

MODEL = "qwen2.5-coder:3b"


def get_metrics():
    return Path("docs/metrics.md").read_text()


def generate_sql(question):
    schema = get_schema()
    metrics = get_metrics()

    prompt = f"""
You are a SQL analyst working with an Olist e-commerce database.

DATABASE SCHEMA:
{schema}

BUSINESS METRIC DEFINITIONS:
{metrics}

RULES:
- Generate exactly one complete SQL SELECT statement.
- The query must always begin with SELECT.
- Use DuckDB SQL syntax.
- For date differences in days, use DATEDIFF('day', start_date, end_date).
- Use only tables and columns that exist in the schema.
- Follow the business metric definitions when answering questions about defined metrics.
- Do not modify, delete, or create any data.
- Return ONLY the SQL query.
- Do not use markdown code fences.
- Do not explain the query.

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


def correct_sql(question, sql, error):
    schema = get_schema()
    metrics = get_metrics()

    prompt = f"""
You are correcting a SQL query for an Olist e-commerce database.

DATABASE SCHEMA:
{schema}

BUSINESS METRIC DEFINITIONS:
{metrics}

BUSINESS QUESTION:
{question}

PREVIOUS SQL:
{sql}

VALIDATION ERROR:
{error}

RULES:
- Return exactly one complete SQL SELECT statement.
- Use DuckDB SQL syntax.
- Fix the validation error.
- Follow the business metric definitions.
- For date differences in days, use DATEDIFF('day', start_date, end_date).
- Use only tables and columns that exist in the schema.
- Do not modify, delete, or create any data.
- Return ONLY the corrected SQL query.
- Do not use markdown code fences.
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


def generate_valid_sql(question, max_attempts=2):
    sql = generate_sql(question)

    for attempt in range(max_attempts):
        try:
            validate_sql(sql)

            # Also test whether DuckDB can actually execute it.
            run_safe_query(sql)

            return sql

        except Exception as e:
            print(f"\nSQL attempt {attempt + 1} failed:")
            print(e)

            if attempt == max_attempts - 1:
                raise ValueError(
                    f"SQL could not be generated successfully after "
                    f"{max_attempts} attempts.\n"
                    f"Last SQL:\n{sql}"
                )

            print("\nAsking the LLM to correct the SQL...")

            sql = correct_sql(
                question=question,
                sql=sql,
                error=str(e)
            )

    return sql


if __name__ == "__main__":
    question = "What is the average delivery time in days?"

    bad_sql = """
    SELECT AVG(DATEDIFF(order_purchase_timestamp, order_delivered_customer_date))
    AS average_delivery_time
    FROM olist_orders_dataset
    WHERE order_delivered_customer_date IS NOT NULL
    """

    print("\nBad SQL:\n")
    print(bad_sql)

    try:
        validate_sql(bad_sql)
        print("\nValidation: PASSED")

    except Exception as e:
        print("\nValidation: FAILED")
        print(e)

        corrected_sql = correct_sql(
            question=question,
            sql=bad_sql,
            error=str(e)
        )

        print("\nCorrected SQL:\n")
        print(corrected_sql)

        result = run_safe_query(corrected_sql)
        validate_result(result)

        print("\nResult:\n")
        print(result)