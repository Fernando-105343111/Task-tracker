"""Validation shared by task creation, full editing and status updates."""

import re
from datetime import date

STATUSES = ("To Do", "In Progress", "Done")
PRIORITIES = ("Low", "Medium", "High")


def validate_status(value):
    if not isinstance(value, str) or value not in STATUSES:
        raise ValueError("Status must be To Do, In Progress or Done")
    return value


def validate_priority(value):
    if not isinstance(value, str) or value not in PRIORITIES:
        raise ValueError("Priority must be Low, Medium or High")
    return value


def validate_due_date(value):
    if value is None or value == "":
        return None
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("Due date must be a valid YYYY-MM-DD date or null")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError("Due date must be a valid YYYY-MM-DD date or null") from None


def validate_task(payload, *, require_all=False):
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object")
    if require_all and not {"title", "description", "status"}.issubset(payload):
        raise ValueError("PUT requires title, description and status")
    title = payload.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Title is required")
    title = title.strip()
    if len(title) > 200:
        raise ValueError("Title must contain at most 200 characters")
    description = payload.get("description", "")
    if not isinstance(description, str):
        raise ValueError("Description must be text")
    if len(description) > 2000:
        raise ValueError("Description must contain at most 2000 characters")
    status = validate_status(payload.get("status", "To Do"))
    priority = validate_priority(payload.get("priority", "Medium"))
    if "dueDate" in payload and "due_date" in payload:
        raise ValueError("Provide dueDate or due_date, not both")
    due_date = validate_due_date(payload.get("dueDate", payload.get("due_date")))
    return {
        "title": title,
        "description": description,
        "status": status,
        "priority": priority,
        "due_date": due_date,
    }
