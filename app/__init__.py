"""Flask application factory for the team's task tracker."""

import os

import psycopg
from flask import Flask, jsonify
from psycopg.conninfo import make_conninfo
from werkzeug.exceptions import HTTPException

from . import db


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE_URL=os.getenv("DATABASE_URL")
        or make_conninfo(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "tasktracker"),
            user=os.getenv("DB_USER", "tasktracker"),
            password=os.getenv("DB_PASSWORD", ""),
        ),
        COMMIT_SHA=os.getenv("COMMIT_SHA", "development"),
        MAX_CONTENT_LENGTH=64 * 1024,
    )
    if test_config is not None:
        app.config.update(test_config)

    db.init_app(app)
    from .routes import bp

    app.register_blueprint(bp)

    @app.errorhandler(HTTPException)
    def http_error(error):
        response = error.get_response()
        response.data = app.json.dumps({"error": error.description})
        response.content_type = "application/json"
        return response

    @app.errorhandler(psycopg.Error)
    def database_error(error):
        # Do not return connection strings or database error details to users.
        app.logger.error("Database operation failed: %s", type(error).__name__)
        return jsonify(error="Database temporarily unavailable"), 503

    return app
