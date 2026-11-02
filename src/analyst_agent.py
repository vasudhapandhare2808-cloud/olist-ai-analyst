import json

import ollama

from src.text_to_sql import generate_valid_sql
from src.safe_sql import run_safe_query
from src.result_validator import validate_result
from src.answer_formatter import format_answer
from src.question_validator import validate_question


MODEL = "llama3.2:3b"
MAX_TOOL_ROUNDS = 3


# ==================================================
# BUSINESS QUERY TOOL
# ==================================================

def run_business_query(question: str) -> str:
    """
    Generate, validate, execute, and format a business query.

    Returns a JSON string containing the SQL and query results.
    """

    try:
        # Generate SQL and validate it.
        sql = generate_valid_sql(question, max_attempts=2)

        print("\n--- GENERATED SQL ---")
        print(sql)

        # Execute the query.
        result = run_safe_query(sql)

        # Validate the query result.
        validate_result(result)

        # Convert DataFrame into JSON-compatible records.
        rows = result.to_dict(orient="records")

        return json.dumps(
            {
                "success": True,
                "sql": sql,
                "rows": rows
            },
            default=str
        )

    except Exception as error:
        return json.dumps(
            {
                "success": False,
                "error": str(error)
            }
        )


# ==================================================
# OLLAMA TOOL DEFINITION
# ==================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_business_query",
            "description": (
                "Answer business questions using the Olist "
                "e-commerce database. Use this tool for questions "
                "about sales, customers, orders, products, reviews, "
                "payments, and delivery."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": (
                            "The business question to answer "
                            "using the database."
                        )
                    }
                },
                "required": ["question"]
            }
        }
    }
]


# ==================================================
# AI ANALYST
# ==================================================

def ask_analyst_response(question: str) -> dict:
    """
    Run the AI analyst and return structured response data.

    Returns:
        {
            "answer": str,
            "sql": str | None,
            "rows": list
        }
    """

    # Validate the user's question.
    is_valid, reason = validate_question(question)

    if not is_valid:
        return {
            "answer": reason,
            "sql": None,
            "rows": []
        }

    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI data analyst for the Olist "
                "e-commerce database. "
                "Use the run_business_query tool to answer "
                "database-related questions. "
                "Do not write SQL yourself. "
                "Do not invent database results."
            )
        },
        {
            "role": "user",
            "content": question
        }
    ]

    for round_number in range(MAX_TOOL_ROUNDS):

        response = ollama.chat(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            options={
                "temperature": 0
            }
        )

        message = response.message

        # No tool call was requested.
        if not message.tool_calls:
            return {
                "answer": (
                    message.content
                    or "The model returned no answer."
                ),
                "sql": None,
                "rows": []
            }

        messages.append(message)

        for tool_call in message.tool_calls:

            tool_name = tool_call.function.name
            arguments = tool_call.function.arguments

            # Validate the requested tool.
            if tool_name != "run_business_query":
                return {
                    "answer": (
                        "The analyst requested an unknown tool."
                    ),
                    "sql": None,
                    "rows": []
                }

            if not isinstance(arguments, dict):
                return {
                    "answer": (
                        "The analyst supplied invalid tool arguments."
                    ),
                    "sql": None,
                    "rows": []
                }

            tool_question = arguments.get("question")

            if (
                not isinstance(tool_question, str)
                or not tool_question.strip()
            ):
                return {
                    "answer": (
                        "The analyst supplied an invalid question."
                    ),
                    "sql": None,
                    "rows": []
                }

            print(f"\n--- TOOL ROUND {round_number + 1} ---")
            print("Business question:", tool_question)

            # Execute the database query.
            raw_result = run_business_query(tool_question)

            try:
                tool_result = json.loads(raw_result)

            except json.JSONDecodeError:
                return {
                    "answer": "Invalid response returned by the query tool.",
                    "sql": None,
                    "rows": []
                }

            print(
                "Tool result:",
                json.dumps(
                    tool_result,
                    ensure_ascii=False
                )
            )

            # Handle query failures.
            if not tool_result.get("success"):
                error = tool_result.get(
                    "error",
                    "Unknown query error."
                )

                return {
                    "answer": (
                        f"The query could not be completed. "
                        f"Reason: {error}"
                    ),
                    "sql": None,
                    "rows": []
                }

            rows = tool_result.get("rows", [])
            sql = tool_result.get("sql")

            if not isinstance(rows, list):
                return {
                    "answer": "Invalid query result format.",
                    "sql": sql,
                    "rows": []
                }

            # Format the result using the existing formatter.
            answer = format_answer(rows)

            return {
                "answer": answer,
                "sql": sql,
                "rows": rows
            }

    return {
        "answer": (
            "The analyst stopped after reaching "
            "the maximum tool-call rounds."
        ),
        "sql": None,
        "rows": []
    }


# ==================================================
# BACKWARD-COMPATIBLE FUNCTION
# ==================================================

def ask_analyst(question: str) -> str:
    """
    Return only the answer text.

    Preserves compatibility with existing tests and CLI usage.
    """

    response = ask_analyst_response(question)

    return response["answer"]


# ==================================================
# COMMAND LINE INTERFACE
# ==================================================

def main():

    question = input(
        "\nAsk your Olist business question: "
    )

    response = ask_analyst_response(question)

    print("\n--- ANALYST ANSWER ---")
    print(response["answer"])

    if response.get("sql"):
        print("\n--- GENERATED SQL ---")
        print(response["sql"])


if __name__ == "__main__":
    main()