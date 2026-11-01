
import pandas as pd


def validate_result(result):
    """
    Validate the basic quality of a SQL query result.

    Checks:
    1. Result is a pandas DataFrame.
    2. Result contains rows.
    3. Result does not contain NULL values.
    """

    if not isinstance(result, pd.DataFrame):
        raise TypeError("Query result must be a pandas DataFrame.")

    if result.empty:
        raise ValueError("Query returned no rows.")

    if result.isnull().values.any():
        raise ValueError("Query result contains NULL values.")

    return True
