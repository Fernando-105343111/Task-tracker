import psycopg
import pytest

pytestmark = pytest.mark.unit


def test_health_and_version_do_not_require_database(unit_app):
    client = unit_app.test_client()
    assert client.get("/health").json == {"status": "ok", "commit": "unit-commit"}
    assert client.get("/version").json == {"commit": "unit-commit"}


def test_home_displays_commit_identifier(unit_app):
    response = unit_app.test_client().get("/")
    assert response.status_code == 200
    assert b"unit-commit" in response.data


def test_unknown_route_returns_json(unit_app):
    response = unit_app.test_client().get("/missing")
    assert response.status_code == 404
    assert "error" in response.json


def test_ready_reports_database_failure_without_leaking_details(unit_app, monkeypatch):
    def unavailable():
        raise psycopg.OperationalError("private-password-and-host")

    monkeypatch.setattr("app.routes.get_db", unavailable)
    response = unit_app.test_client().get("/ready")
    assert response.status_code == 503
    assert response.json["database"] == "unavailable"
    assert b"private-password" not in response.data


def test_task_database_failure_returns_service_unavailable(unit_app, monkeypatch):
    def unavailable():
        raise psycopg.OperationalError("private-password-and-host")

    monkeypatch.setattr("app.routes.get_db", unavailable)
    response = unit_app.test_client().get("/api/tasks")
    assert response.status_code == 503
    assert response.json == {"error": "Database temporarily unavailable"}
