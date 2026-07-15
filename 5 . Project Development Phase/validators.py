"""
validators.py
--------------
Central place for all input validation logic used by both the Streamlit
front-end and the Flask prediction API. Keeping validation here means the
UI and the API always agree on what counts as a "valid" application.

Every validator returns a tuple: (is_valid: bool, error_message: str or None)
"""

import re

# ---------------------------------------------------------------------------
# Text field rules
# ---------------------------------------------------------------------------
NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z .'-]{1,49}$")
JOB_TITLE_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9 .,'/&-]{1,59}$")

# ---------------------------------------------------------------------------
# Numeric field rules (inclusive ranges)
# ---------------------------------------------------------------------------
RANGES = {
    "age": (18, 100),
    "annual_income": (0, 10_000_000),
    "credit_score": (300, 850),
    "existing_debt": (0, 10_000_000),
    "employment_years": (0, 70),
}


def validate_name(name):
    """Full legal name: letters, spaces, apostrophes, hyphens, periods. 2-50 chars."""
    if name is None or not isinstance(name, str) or name.strip() == "":
        return False, "Name is required."
    name = name.strip()
    if len(name) < 2:
        return False, "Name must be at least 2 characters long."
    if len(name) > 50:
        return False, "Name must be 50 characters or fewer."
    if not NAME_PATTERN.match(name):
        return False, "Name may only contain letters, spaces, apostrophes, hyphens, and periods."
    return True, None


def validate_job_title(title):
    """Job title: letters/numbers and common punctuation. 2-60 chars."""
    if title is None or not isinstance(title, str) or title.strip() == "":
        return False, "Job title is required."
    title = title.strip()
    if len(title) < 2:
        return False, "Job title must be at least 2 characters long."
    if len(title) > 60:
        return False, "Job title must be 60 characters or fewer."
    if not JOB_TITLE_PATTERN.match(title):
        return False, "Job title contains invalid characters."
    return True, None


def _validate_numeric_range(value, field_key, field_label, allow_float=True):
    low, high = RANGES[field_key]
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return False, f"{field_label} is required."
    try:
        numeric_value = float(value) if allow_float else int(value)
    except (TypeError, ValueError):
        return False, f"{field_label} must be a number."
    if numeric_value != numeric_value:  # NaN check
        return False, f"{field_label} must be a valid number."
    if numeric_value < low or numeric_value > high:
        return False, f"{field_label} must be between {low} and {high}."
    return True, None


def validate_age(age):
    return _validate_numeric_range(age, "age", "Age", allow_float=False)


def validate_income(income):
    return _validate_numeric_range(income, "annual_income", "Annual income", allow_float=True)


def validate_credit_score(score):
    return _validate_numeric_range(score, "credit_score", "Credit score", allow_float=False)


def validate_existing_debt(debt):
    return _validate_numeric_range(debt, "existing_debt", "Existing debt", allow_float=True)


def validate_employment_years(years):
    return _validate_numeric_range(years, "employment_years", "Years employed", allow_float=True)


def validate_application(data: dict):
    """
    Validate an entire application payload.

    Parameters
    ----------
    data : dict with keys name, job_title, age, annual_income,
           credit_score, existing_debt, employment_years

    Returns
    -------
    (is_valid: bool, errors: dict[field] = message)
    """
    checks = {
        "name": validate_name(data.get("name")),
        "job_title": validate_job_title(data.get("job_title")),
        "age": validate_age(data.get("age")),
        "annual_income": validate_income(data.get("annual_income")),
        "credit_score": validate_credit_score(data.get("credit_score")),
        "existing_debt": validate_existing_debt(data.get("existing_debt")),
        "employment_years": validate_employment_years(data.get("employment_years")),
    }

    errors = {field: msg for field, (ok, msg) in checks.items() if not ok}
    return (len(errors) == 0), errors
