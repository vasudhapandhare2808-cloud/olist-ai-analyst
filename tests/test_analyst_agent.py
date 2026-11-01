
import json
from types import SimpleNamespace
from unittest.mock import patch

from src.analyst_agent import ask_analyst, run_business_query


def test_unsupported_salary_question():
    """Unsupported questions should be rejected before calling Ollama."""
    with patch("src.analyst_agent.ollama.chat") as mock_chat:
        answer = ask_analyst(
            "What is the average salary of employees?"
        )

    assert "salary" in answer.lower()
    mock_chat.assert_not_called()


def test_empty_question():
    """An empty question should return a helpful message."""
    answer = ask_analyst("   ")

    assert "enter a business question" in answer.lower()


def test_total_orders_answer_is_exact():
    """The agent should report the exact count returned by the tool."""
    tool_result = {
        "success": True,
        "sql": "SELECT COUNT(*) FROM olist_orders_dataset;",
        "rows": [{"count_star()": 99441}],
    }

    mock_tool_call = SimpleNamespace(
        function=SimpleNamespace(
            name="run_business_query",
            arguments={
                "question": "How many orders are there in total?"
            },
        )
    )

    mock_message = SimpleNamespace(
        tool_calls=[mock_tool_call],
        content="",
    )

    mock_response = SimpleNamespace(message=mock_message)

    with (
        patch(
            "src.analyst_agent.run_business_query",
            return_value=json.dumps(tool_result),
        ),
        patch(
            "src.analyst_agent.ollama.chat",
            return_value=mock_response,
        ) as mock_chat,
    ):
        answer = ask_analyst(
            "How many orders are there in total?"
        )

    assert answer == "The result for count star() is 99,441."
    mock_chat.assert_called_once()


def test_failed_query_returns_clear_error():
    """SQL generation failures should be returned as structured errors."""
    with patch(
        "src.analyst_agent.generate_valid_sql",
        side_effect=RuntimeError("SQL generation failed"),
    ):
        result = json.loads(
            run_business_query(
                "Show me an unsupported metric"
            )
        )

    assert result["success"] is False
    assert "SQL generation failed" in result["error"]


if __name__ == "__main__":
    test_unsupported_salary_question()
    print("PASS: unsupported salary question")

    test_empty_question()
    print("PASS: empty question")

    test_total_orders_answer_is_exact()
    print("PASS: exact total orders answer")

    test_failed_query_returns_clear_error()
    print("PASS: failed query error handling")

    print("\nALL 4 ANALYST AGENT TESTS PASSED")
