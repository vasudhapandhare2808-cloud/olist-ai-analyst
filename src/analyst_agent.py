
import json
import ollama

from src.text_to_sql import generate_valid_sql
from src.safe_sql import run_safe_query
from src.result_validator import validate_result
from src.question_validator import validate_question


MODEL = "llama3.2:3b"
MAX_TOOL_ROUNDS = 3


def run_business_query(question: str) -> str:
    """Generate validated SQL, execute it, and return database results."""

    try:
        sql = generate_valid_sql(question, max_attempts=2)

        print("\n--- VALIDATED SQL ---")
        print(sql)

        result = run_safe_query(sql)
        validate_result(result)

        rows = json.loads(result.to_json(orient="records"))

        return json.dumps(
            {
                "success": True,
                "sql": sql,
                "rows": rows,
            },
            ensure_ascii=False,
        )

    except Exception as exc:
        return json.dumps(
            {
                "success": False,
                "error": str(exc),
            },
            ensure_ascii=False,
        )


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_business_query",
            "description": (
                "Answer a business question by generating validated SQL "
                "with the existing Text-to-SQL pipeline and querying "
                "the Olist database. Pass the user's business question."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The business question to answer.",
                    }
                },
                "required": ["question"],
            },
        },
    }
]


def ask_analyst(question: str) -> str:
    """Validate the question, execute tools, and return a reliable answer."""

    is_valid, reason = validate_question(question)

    if not is_valid:
        return reason

    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI data analyst for the Olist e-commerce "
                "database. Call run_business_query to answer database "
                "questions. Do not write SQL yourself. "
                "Use only successful tool results. Copy numeric values "
                "exactly as supplied; never invent or alter them. "
                "Do not claim a query succeeded if it failed."
            ),
        },
        {
            "role": "user",
            "content": question,
        },
    ]

    for round_number in range(MAX_TOOL_ROUNDS):
        response = ollama.chat(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            options={"temperature": 0},
        )

        message = response.message

        if not message.tool_calls:
            return message.content or "The model returned no answer."

        messages.append(message)

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            arguments = tool_call.function.arguments

            if tool_name != "run_business_query":
                return (
                    "The analyst requested an unknown tool. "
                    "The query was not completed."
                )

            if not isinstance(arguments, dict):
                return "The analyst supplied invalid tool arguments."

            tool_question = arguments.get("question")

            if (
                not isinstance(tool_question, str)
                or not tool_question.strip()
            ):
                return "The analyst supplied an empty or invalid business question."

            print(f"\n--- TOOL ROUND {round_number + 1} ---")
            print("Business question:", tool_question)

            raw_result = run_business_query(tool_question)
            tool_result = json.loads(raw_result)

            print(
                "Tool result:",
                json.dumps(tool_result, ensure_ascii=False),
            )

            # Failures are handled directly by Python.
            if not tool_result.get("success"):
                error = tool_result.get(
                    "error",
                    "Unknown query error.",
                )
                return f"The query could not be completed. Reason: {error}"

            # Targeted exact answer for the total-order count.
            sql = tool_result.get("sql", "").strip().rstrip(";").lower()
            rows = tool_result.get("rows", [])

            if (
                sql == "select count(*) from olist_orders_dataset"
                and len(rows) == 1
                and "count_star()" in rows[0]
            ):
                count = rows[0]["count_star()"]
                return f"There are {count:,} orders in total."

            # Other successful queries are explained by the language model.
            messages.append(
                {
                    "role": "tool",
                    "name": tool_name,
                    "content": json.dumps(
                        tool_result,
                        ensure_ascii=False,
                    ),
                }
            )

    return "The analyst stopped after reaching the maximum tool-call rounds."


def main():
    question = input("Ask your Olist AI Analyst: ").strip()

    if not question:
        print("Please enter a business question.")
        return

    try:
        answer = ask_analyst(question)
        print("\n--- ANALYST ANSWER ---")
        print(answer)

    except Exception as exc:
        print(f"Analyst error: {exc}")


if __name__ == "__main__":
    main()
