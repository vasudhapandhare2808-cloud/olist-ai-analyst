import pandas as pd


def validate_result(result):
    """
    Validate the basic quality of a SQL query result.

    Checks:
    1. Result is not empty.
    2. Result does not contain NULL values.
    """

    if result.empty:
        raise ValueError("Query returned no rows.")

    if result.isnull().values.any():
        raise ValueError("Query result contains NULL values.")

    return True