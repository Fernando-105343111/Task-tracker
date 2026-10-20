from datetime import date

import pytest

from app.validation import validate_due_date, validate_priority, validate_task

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("priority", ["Low", "Medium", "High"])
def test_supported_priorities(priority):
    assert validate_priority(priority) == priority


@pytest.mark.parametrize("priority", ["Urgent", "high", "", None, 1, True, [], {}])
def test_invalid_priorities(priority):
    with pytest.raises(ValueError, match="Priority must"):
        validate_priority(priority)


@pytest.mark.parametrize("value", [None, ""])
def test_due_date_can_be_unset(value):
    assert validate_due_date(value) is None


@pytest.mark.parametrize("value", ["2026-10-19", "2028-02-29", "2020-01-01"])
def test_real_iso_dates_are_accepted(value):
    assert validate_due_date(value) == date.fromisoformat(value)


@pytest.mark.parametrize(
    "value",
    ["2026-02-29", "2026-02-30", "2026-13-01", "20261019", "19/10/2026", "2026-1-1", 1, [], {}],
)
def test_invalid_due_dates_are_rejected(value):
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        validate_due_date(value)


def test_snake_case_due_date_is_accepted_as_an_input_alias():
    assert validate_task({"title": "Task", "due_date": "2026-12-01"})["due_date"] == date(
        2026, 12, 1
    )


def test_ambiguous_date_fields_are_rejected():
    with pytest.raises(ValueError, match="not both"):
        validate_task({"title": "Task", "dueDate": None, "due_date": "2026-12-01"})


@pytest.mark.parametrize("missing", ["title", "description", "status"])
def test_full_edit_requires_all_core_fields(missing):
    payload = {"title": "Task", "description": "Description", "status": "Done"}
    del payload[missing]
    with pytest.raises(ValueError, match="PUT requires"):
        validate_task(payload, require_all=True)
