"""HTTP contract for the frontend, acceptance tests and deployment checks."""

import psycopg
from flask import Blueprint, abort, current_app, jsonify, render_template, request

from .db import get_db
from .validation import validate_status, validate_task

bp = Blueprint("tasks", __name__)


@bp.get("/")
def index():
    return render_template("index.html", commit_sha=current_app.config["COMMIT_SHA"])


@bp.get("/health")
def health():
    return jsonify(status="ok", commit=current_app.config["COMMIT_SHA"])


@bp.get("/ready")
def ready():
    try:
        get_db().execute("SELECT 1").fetchone()
    except psycopg.Error:
        return jsonify(status="not ready", database="unavailable"), 503
    return jsonify(status="ready", database="connected")


@bp.get("/version")
def version():
    return jsonify(commit=current_app.config["COMMIT_SHA"])


@bp.get("/api/tasks")
def list_tasks():
    rows = (
        get_db().execute("SELECT id, title, description, status FROM tasks ORDER BY id").fetchall()
    )
    return jsonify(rows)


@bp.post("/api/tasks")
def create_task():
    try:
        values = validate_task(request.get_json())
    except ValueError as error:
        abort(400, description=str(error))
    row = (
        get_db()
        .execute(
            "INSERT INTO tasks (title, description, status) VALUES (%s, %s, %s) "
            "RETURNING id, title, description, status",
            (values["title"], values["description"], values["status"]),
        )
        .fetchone()
    )
    return jsonify(row), 201, {"Location": f"/api/tasks/{row['id']}"}


@bp.get("/api/tasks/<int:task_id>")
def get_task(task_id):
    row = (
        get_db()
        .execute("SELECT id, title, description, status FROM tasks WHERE id = %s", (task_id,))
        .fetchone()
    )
    if row is None:
        abort(404, description="Task not found")
    return jsonify(row)


@bp.patch("/api/tasks/<int:task_id>")
def update_task_status(task_id):
    payload = request.get_json()
    if not isinstance(payload, dict) or set(payload) != {"status"}:
        abort(400, description="Provide only the status field")
    try:
        status = validate_status(payload["status"])
    except ValueError as error:
        abort(400, description=str(error))
    row = (
        get_db()
        .execute(
            "UPDATE tasks SET status = %s WHERE id = %s RETURNING id, title, description, status",
            (status, task_id),
        )
        .fetchone()
    )
    if row is None:
        abort(404, description="Task not found")
    return jsonify(row)


@bp.delete("/api/tasks/<int:task_id>")
def delete_task(task_id):
    row = get_db().execute("DELETE FROM tasks WHERE id = %s RETURNING id", (task_id,)).fetchone()
    if row is None:
        abort(404, description="Task not found")
    return "", 204
