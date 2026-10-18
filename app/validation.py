"""Validation shared by task creation and status updates."""

STATUSES = ("To Do", "In Progress", "Done")


def validate_status(value):
    if not isinstance(value, str) or value not in STATUSES:
        raise ValueError("Status must be To Do, In Progress or Done")
    return value


def validate_task(payload):
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object")
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
    return {"title": title, "description": description, "status": status}
