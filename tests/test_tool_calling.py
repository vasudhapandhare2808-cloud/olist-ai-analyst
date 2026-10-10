
import json
import ollama

from src.safe_sql import run_safe_query
from src.result_validator import validate_result

MODEL = "llama3.2:3b"
MAX_TOOL_ROUNDS = 3


def run_business_query(sql: str) -> str:
    """Execute a read-only SQL query and return validated results."""

    try:
        result = run_safe_query(sql)
        validate_result(result)

        return json.dumps({
            "success": True,
            "rows": json.loads(result.to_json(orient="records")),
        })

    except (ValueError, Exception) as exc:
        return json.dumps({
            "success": False,
            "error": str(exc),
        })


tools = [
    {
        "type": "function",
        "function": {
            "name": "run_business_query",
            "description": (
                "Run a read-only SQL SELECT query against the Olist "
                "database and return its results or a controlled error."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "A SQL SELECT query.",
                    }
                },
                "required": ["sql"],
            },
        },
    }
]

messages = [
    {
        "role": "user",
        "content": (
            "Use run_business_query to count all rows in "
            "olist_orders_dataset. Give me the total number of orders."
        ),
    }
]

for round_number in range(MAX_TOOL_ROUNDS):
    response = ollama.chat(
        model=MODEL,
        messages=messages,
        tools=tools,
        options={"temperature": 0},
    )

    message = response.message
    messages.append(message)

    if not message.tool_calls:
        print("\n--- FINAL ANSWER ---")
        print(message.content or "(No final answer returned.)")
        break

    for tool_call in message.tool_calls:
        if tool_call.function.name != "run_business_query":
            tool_result = json.dumps({
                "success": False,
                "error": "Unknown tool requested.",
            })
        else:
            arguments = tool_call.function.arguments

            if not isinstance(arguments, dict):
                tool_result = json.dumps({
                    "success": False,
                    "error": "Tool arguments must be an object.",
                })
            elif not isinstance(arguments.get("sql"), str):
                tool_result = json.dumps({
                    "success": False,
                    "error": "The sql argument must be a string.",
                })
            else:
                sql = arguments["sql"]
                print(f"\n--- TOOL ROUND {round_number + 1} ---")
                print("SQL:", sql)

                tool_result = run_business_query(sql)

        print("Tool result:", tool_result)

        messages.append({
            "role": "tool",
            "name": tool_call.function.name,
            "content": tool_result,
        })

else:
    print("\nStopped: maximum tool-call rounds reached.")
