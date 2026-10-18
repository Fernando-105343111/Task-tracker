import psycopg
import pytest

from app import create_app
from app.db import get_db

pytestmark = pytest.mark.integration


def test_database_is_postgresql_and_readiness_succeeds(app, client):
    with app.app_context():
        result = get_db().execute("SELECT version() AS version").fetchone()
        assert "PostgreSQL" in result["version"]
    assert client.get("/ready").json == {"status": "ready", "database": "connected"}


def test_full_task_lifecycle(client):
    assert client.get("/api/tasks").json == []
    created = client.post(
        "/api/tasks", json={"title": "Demo task", "description": "Verify database"}
    )
    assert created.status_code == 201
    task = created.json
    assert task == {
        "id": task["id"],
        "title": "Demo task",
        "description": "Verify database",
        "status": "To Do",
    }
    url = created.headers["Location"]
    assert client.get(url).json == task
    assert client.get("/api/tasks").json == [task]
    for status in ("In Progress", "Done"):
        response = client.patch(url, json={"status": status})
        assert response.status_code == 200
        assert client.get(url).json["status"] == status
    assert client.delete(url).status_code == 204
    assert client.get(url).status_code == 404
    assert client.get("/api/tasks").json == []


def test_task_survives_new_application_instance(app, client):
    task = client.post("/api/tasks", json={"title": "Persisted task"}).json
    second = create_app({"TESTING": True, "DATABASE_URL": app.config["DATABASE_URL"]})
    assert second.test_client().get(f"/api/tasks/{task['id']}").json == task


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": " "},
        {"title": "x", "status": "Blocked"},
        {"title": "x", "description": None},
        [],
        None,
    ],
)
def test_invalid_create_does_not_insert_task(client, payload):
    response = (
        client.post("/api/tasks", json=payload)
        if payload is not None
        else client.post("/api/tasks", data="null", content_type="application/json")
    )
    assert response.status_code == 400
    assert "error" in response.json
    assert client.get("/api/tasks").json == []


def test_malformed_json_and_wrong_content_type_are_rejected(client):
    assert client.post("/api/tasks", data="{", content_type="application/json").status_code == 400
    assert client.post("/api/tasks", data="title=x").status_code == 415


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_missing_task_is_404(client, method):
    kwargs = {"json": {"status": "Done"}} if method == "patch" else {}
    response = getattr(client, method)("/api/tasks/999999", **kwargs)
    assert response.status_code == 404
    assert response.json["error"] == "Task not found"


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"status": "Blocked"},
        {"title": "Changed"},
        {"status": "Done", "title": "Changed"},
        [],
        {"status": None},
    ],
)
def test_invalid_update_preserves_original_record(client, payload):
    created = client.post("/api/tasks", json={"title": "Original"})
    url = created.headers["Location"]
    assert client.patch(url, json=payload).status_code == 400
    assert client.get(url).json == created.json


def test_sql_syntax_in_title_is_saved_as_data(client):
    title = "Robert'); DROP TABLE tasks; --"
    created = client.post("/api/tasks", json={"title": title})
    assert created.status_code == 201
    assert client.get(created.headers["Location"]).json["title"] == title
    assert client.post("/api/tasks", json={"title": "Next task"}).status_code == 201


def test_database_constraint_rejects_invalid_status(app):
    with app.app_context():
        with pytest.raises(psycopg.errors.CheckViolation):
            get_db().execute(
                "INSERT INTO tasks (title, status) VALUES (%s, %s)", ("Task", "Blocked")
            )


def test_database_initialisation_preserves_saved_tasks(app, client):
    created = client.post("/api/tasks", json={"title": "Keep me"})
    result = app.test_cli_runner().invoke(args=["init-db"])
    assert result.exit_code == 0
    assert "initialised" in result.output
    assert client.get(created.headers["Location"]).json == created.json
