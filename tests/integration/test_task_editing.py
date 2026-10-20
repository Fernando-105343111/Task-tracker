from pathlib import Path

import pytest

from app import create_app
from app.db import get_db

pytestmark = pytest.mark.integration


def create_details(client):
    return client.post(
        "/api/tasks",
        json={
            "title": "Original",
            "description": "Before edit",
            "status": "To Do",
            "priority": "Low",
            "dueDate": "2026-12-01",
        },
    )


def test_create_get_and_list_include_persisted_details(client):
    response = create_details(client)
    assert response.status_code == 201
    task = response.json
    assert task["priority"] == "Low"
    assert task["dueDate"] == "2026-12-01"
    assert client.get(response.headers["Location"]).json == task
    assert client.get("/api/tasks").json == [task]


@pytest.mark.parametrize("endpoint", ["resource", "collection", "collection_slash"])
def test_full_edit_returns_and_persists_updated_task(client, endpoint):
    created = create_details(client)
    task_id = created.json["id"]
    payload = {
        "title": "Edited",
        "description": "After edit",
        "status": "In Progress",
        "priority": "High",
        "dueDate": "2028-02-29",
    }
    url = created.headers["Location"]
    if endpoint != "resource":
        payload["id"] = task_id
        url = "/api/tasks/" if endpoint == "collection_slash" else "/api/tasks"
    updated = client.put(url, json=payload)
    assert updated.status_code == 200
    expected = {
        "id": task_id,
        "title": "Edited",
        "description": "After edit",
        "status": "In Progress",
        "priority": "High",
        "dueDate": "2028-02-29",
    }
    assert updated.json == expected
    assert client.get(created.headers["Location"]).json == expected


def test_edit_survives_a_new_application_instance(app, client):
    created = create_details(client)
    client.put(
        created.headers["Location"],
        json={
            "title": "Stored edit",
            "description": "Saved",
            "status": "Done",
            "priority": "High",
            "dueDate": "2027-01-02",
        },
    )
    second = create_app({"TESTING": True, "DATABASE_URL": app.config["DATABASE_URL"]})
    saved = second.test_client().get(created.headers["Location"]).json
    assert saved["title"] == "Stored edit"
    assert saved["priority"] == "High"
    assert saved["dueDate"] == "2027-01-02"


def test_core_only_edit_preserves_optional_values(client):
    created = create_details(client)
    response = client.put(
        created.headers["Location"],
        json={
            "title": "Edited",
            "description": "New description",
            "status": "Done",
        },
    )
    assert response.status_code == 200
    assert response.json["priority"] == "Low"
    assert response.json["dueDate"] == "2026-12-01"


@pytest.mark.parametrize("value", [None, ""])
def test_edit_can_clear_due_date(client, value):
    created = create_details(client)
    response = client.put(
        created.headers["Location"],
        json={
            "title": "Edited",
            "description": "",
            "status": "To Do",
            "dueDate": value,
        },
    )
    assert response.status_code == 200
    assert response.json["dueDate"] is None
    assert client.get(created.headers["Location"]).json["dueDate"] is None


def test_snake_case_date_alias_works_for_create_and_edit(client):
    created = client.post("/api/tasks", json={"title": "Task", "due_date": "2026-12-01"})
    assert created.json["dueDate"] == "2026-12-01"
    updated = client.put(
        created.headers["Location"],
        json={
            "title": "Task",
            "description": "",
            "status": "Done",
            "due_date": "2027-01-01",
        },
    )
    assert updated.status_code == 200
    assert updated.json["dueDate"] == "2027-01-01"


@pytest.mark.parametrize(
    "field,value",
    [
        ("title", " "),
        ("title", "x" * 201),
        ("description", None),
        ("status", "Blocked"),
        ("priority", "Urgent"),
        ("dueDate", "2026-02-30"),
    ],
)
def test_invalid_edit_is_rejected_without_changing_record(client, field, value):
    created = create_details(client)
    payload = {"title": "Edited", "description": "Changed", "status": "Done"}
    payload[field] = value
    assert client.put(created.headers["Location"], json=payload).status_code == 400
    assert client.get(created.headers["Location"]).json == created.json


@pytest.mark.parametrize("payload", [[], {}, {"title": "Only title"}])
def test_bad_or_incomplete_put_body_is_400(client, payload):
    created = create_details(client)
    assert client.put(created.headers["Location"], json=payload).status_code == 400
    assert client.get(created.headers["Location"]).json == created.json


@pytest.mark.parametrize("task_id", [None, True, "1", 0, -1])
def test_collection_put_requires_positive_integer_id(client, task_id):
    response = client.put(
        "/api/tasks/",
        json={
            "id": task_id,
            "title": "Edited",
            "description": "",
            "status": "Done",
        },
    )
    assert response.status_code == 400


@pytest.mark.parametrize("body_id", [2, True, "1"])
def test_put_cannot_target_a_different_body_id(client, body_id):
    created = create_details(client)
    assert created.json["id"] == 1
    assert (
        client.put(
            created.headers["Location"],
            json={
                "id": body_id,
                "title": "Edited",
                "description": "",
                "status": "Done",
            },
        ).status_code
        == 400
    )


def test_matching_body_id_is_accepted(client):
    created = create_details(client)
    assert (
        client.put(
            created.headers["Location"],
            json={
                "id": created.json["id"],
                "title": "Edited",
                "description": "",
                "status": "Done",
            },
        ).status_code
        == 200
    )


@pytest.mark.parametrize("url", ["/api/tasks/999999", "/api/tasks/"])
def test_missing_task_put_is_404(client, url):
    assert (
        client.put(
            url,
            json={
                "id": 999999,
                "title": "Edited",
                "description": "",
                "status": "Done",
            },
        ).status_code
        == 404
    )


def test_status_patch_preserves_priority_and_due_date(client):
    created = create_details(client)
    updated = client.patch(created.headers["Location"], json={"status": "Done"})
    assert updated.status_code == 200
    assert updated.json["priority"] == "Low"
    assert updated.json["dueDate"] == "2026-12-01"


@pytest.mark.parametrize(
    "payload",
    [
        {"title": "Task", "priority": "Urgent"},
        {"title": "Task", "dueDate": "2026-02-30"},
        {"title": "Task", "dueDate": None, "due_date": None},
    ],
)
def test_bad_details_on_creation_do_not_insert_records(client, payload):
    assert client.post("/api/tasks", json=payload).status_code == 400
    assert client.get("/api/tasks").json == []


def test_migration_upgrades_legacy_database_without_losing_tasks(app, client):
    # app fixture confines these operations to a random schema in the _test DB.
    with app.app_context():
        connection = get_db()
        connection.execute("DROP TABLE tasks")
        connection.execute(Path(app.root_path, "schema.sql").read_text())
        task_id = connection.execute(
            "INSERT INTO tasks (title, description, status) VALUES (%s, %s, %s) RETURNING id",
            ("Existing task", "Keep this record", "In Progress"),
        ).fetchone()["id"]
    runner = app.test_cli_runner()
    assert runner.invoke(args=["init-db"]).exit_code == 0
    assert client.get(f"/api/tasks/{task_id}").json == {
        "id": task_id,
        "title": "Existing task",
        "description": "Keep this record",
        "status": "In Progress",
        "priority": "Medium",
        "dueDate": None,
    }
    assert (
        client.put(
            f"/api/tasks/{task_id}",
            json={
                "title": "Existing task",
                "description": "Keep this record",
                "status": "In Progress",
                "priority": "High",
                "dueDate": "2026-12-01",
            },
        ).status_code
        == 200
    )
    assert runner.invoke(args=["init-db"]).exit_code == 0
    preserved = client.get(f"/api/tasks/{task_id}").json
    assert preserved["priority"] == "High"
    assert preserved["dueDate"] == "2026-12-01"
