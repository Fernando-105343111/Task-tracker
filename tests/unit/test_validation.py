import pytest

from app.validation import STATUSES, validate_status, validate_task

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("status", STATUSES)
def test_accepts_each_supported_status(status):
    assert validate_status(status) == status


@pytest.mark.parametrize("status", ["done", "Blocked", "", None, 3, [], {}])
def test_rejects_unsupported_or_non_text_status(status):
    with pytest.raises(ValueError, match="Status must"):
        validate_status(status)


def test_task_defaults_and_title_whitespace():
    assert validate_task({"title": "  Review brief  "}) == {
        "title": "Review brief",
        "description": "",
        "status": "To Do",
    }


@pytest.mark.parametrize("title", [None, "", "   ", 42, False, []])
def test_title_is_required_text(title):
    with pytest.raises(ValueError, match="Title is required"):
        validate_task({"title": title})


@pytest.mark.parametrize("payload", [None, [], "text", 5])
def test_payload_must_be_an_object(payload):
    with pytest.raises(ValueError, match="JSON object"):
        validate_task(payload)


def test_title_length_boundary():
    assert len(validate_task({"title": "x" * 200})["title"]) == 200
    with pytest.raises(ValueError, match="200 characters"):
        validate_task({"title": "x" * 201})


@pytest.mark.parametrize("description", [None, 42, []])
def test_description_must_be_text(description):
    with pytest.raises(ValueError, match="Description must be text"):
        validate_task({"title": "Task", "description": description})


def test_description_length_boundary():
    assert len(validate_task({"title": "Task", "description": "x" * 2000})["description"]) == 2000
    with pytest.raises(ValueError, match="2000 characters"):
        validate_task({"title": "Task", "description": "x" * 2001})
