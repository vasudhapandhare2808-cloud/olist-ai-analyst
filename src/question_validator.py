
from src.schema import get_schema

# These phrases refer to information that is not represented
# in the current Olist database schema.
UNSUPPORTED_FIELD_TERMS = {
    "salary": ["salary", "salaries", "employee salary", "staff salary"],
    "employee": ["employee", "employees", "staff member", "staff members"],
}


def validate_question(question: str) -> tuple[bool, str]:
    """Check input and detect explicitly unsupported information."""

    if not question or not question.strip():
        return False, "Please enter a business question."

    schema = get_schema()

    if not schema.strip():
        return False, "The database schema could not be retrieved."

    question_lower = question.lower()

    # Check whether the requested information is absent from the schema.
    if any(
        term in question_lower
        for term in UNSUPPORTED_FIELD_TERMS["salary"]
    ):
        return (
            False,
            "Salary information is not available in the current Olist database.",
        )

    if any(
        term in question_lower
        for term in UNSUPPORTED_FIELD_TERMS["employee"]
    ):
        return (
            False,
            "Employee information is not available in the current Olist database.",
        )

    return True, "Question passed the validation check."
