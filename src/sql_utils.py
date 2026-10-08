import re


def extract_sql(text):
    """
    Extract SQL from an LLM response.

    Handles:
    1. Markdown SQL code fences
    2. Plain SQL responses
    """

    text = text.strip()

    fenced = re.search(
        r"```(?:sql)?\s*(.*?)```",
        text,
        re.IGNORECASE | re.DOTALL,
    )

    if fenced:
        return fenced.group(1).strip()

    return text