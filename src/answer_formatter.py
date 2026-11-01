
from typing import Any


def format_value(value: Any) -> str:
    """Convert database values into readable text without changing precision."""

    if value is None:
        return "Not available"

    if isinstance(value, bool):
        return str(value)

    if isinstance(value, int):
        return f"{value:,}"

    if isinstance(value, float):
        return str(value)

    return str(value)


def format_answer(rows: list[dict]) -> str:
    """Convert database rows into a deterministic natural-language answer."""

    if not rows:
        return "The query returned no results."

    if not isinstance(rows, list):
        return "Invalid query result format."

    if not all(isinstance(row, dict) for row in rows):
        return "Invalid query result format."

    if len(rows) == 1:
        row = rows[0]

        if not row:
            return "The query returned an empty result."

        if len(row) == 1:
            column, value = next(iter(row.items()))

            return (
                f"The result for {column.replace('_', ' ')} "
                f"is {format_value(value)}."
            )

        values = [
            f"{column.replace('_', ' ')}: {format_value(value)}"
            for column, value in row.items()
        ]

        return "The results are: " + "; ".join(values) + "."

    output = []

    for index, row in enumerate(rows, start=1):
        values = [
            f"{column.replace('_', ' ')}: {format_value(value)}"
            for column, value in row.items()
        ]

        output.append(f"{index}. " + ", ".join(values))

    return "The query returned the following results:\n" + "\n".join(output)
