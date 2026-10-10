
import json
import re

import ollama

from src.text_to_sql import generate_valid_sql
from src.safe_sql import run_safe_query
from src.result_validator import validate_result


MODEL = "llama3.2:3b"
MAX_TOOL_ROUNDS = 3


def run_business_query(question: str) -> str:
    """Generate validated SQL, execute it, and return actual database results."""

    try:
        sql = generate_valid_sql(question, max_attempts=2)

        print("\n--- VALIDATED SQL ---")
        print(sql)

        result = run_safe_query(sql)
        validate_result(result)

        rows = json.loads(result.to_json(orient="records"))

        tool_result = {
            "success": True,
            "sql": sql,
            "rows": rows,
        }

        return json.dumps(tool_result, ensure_ascii=False)

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
                "and querying the Olist database. Pass the user's "
                "business question."
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
    """Use Llama for tool selection and explanations."""

    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI data analyst for the Olist e-commerce "
                "database. To answer database questions, call the "
                "run_business_query tool and pass the user's question. "
                "Do not write SQL yourself. "
                "Base your answer only on successful tool results. "
                "Copy numeric values exactly as supplied by the tool. "
                "Never change, round, estimate, or invent numbers. "
                "If the tool reports failure, explain that the query "
                "could not be completed. Never claim a failed query "
                "succeeded."
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

        # If the model gives a final response, return it.
        if not message.tool_calls:
            return message.content or "The model returned no answer."

        messages.append(message)

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            arguments = tool_call.function.arguments

            if tool_name != "run_business_query":
                tool_result = {
                    "success": False,
                    "error": "Unknown tool requested.",
                }

            elif not isinstance(arguments, dict):
                tool_result = {
                    "success": False,
                    "error": "Tool arguments must be an object.",
                }

            elif not isinstance(arguments.get("question"), str):
                tool_result = {
                    "success": False,
                    "error": "The question argument must be a string.",
                }

            elif not arguments["question"].strip():
                tool_result = {
                    "success": False,
                    "error": "The question cannot be empty.",
                }

            else:
                print(f"\n--- TOOL ROUND {round_number + 1} ---")
                print("Business question:", arguments["question"])

                raw_result = run_business_query(arguments["question"])
                tool_result = json.loads(raw_result)

            print(
                "Tool result:",
                json.dumps(tool_result, ensure_ascii=False),
            )

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

    return "Stopped after reaching the maximum tool-call rounds."


def main():
    question = input("Ask your Olist AI Analyst: ").strip()

    if not question:
        print("Please enter a question.")
        return

    try:
        answer = ask_analyst(question)

        print("\n--- ANALYST ANSWER ---")
        print(answer)

    except Exception as exc:
        print(f"Analyst error: {exc}")


if __name__ == "__main__":
    main()
