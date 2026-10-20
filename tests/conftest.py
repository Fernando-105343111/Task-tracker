import os
import uuid

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from app import create_app
from app.db import init_db


@pytest.fixture
def unit_app():
    return create_app(
        {
            "TESTING": True,
            "DATABASE_URL": "host=127.0.0.1 port=1 dbname=unused",
            "COMMIT_SHA": "unit-commit",
        }
    )


@pytest.fixture(scope="session")
def postgres_test_url():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        raise pytest.UsageError(
            "Set TEST_DATABASE_URL or run compose.test.yaml; PostgreSQL is required"
        )
    values = conninfo_to_dict(url)
    if not values.get("dbname", "").endswith("_test"):
        raise pytest.UsageError("Integration tests require a database name ending in _test")
    # Each run gets a private schema, including when CI runs share the test server.
    schema = "test_" + uuid.uuid4().hex
    with psycopg.connect(url, autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    try:
        yield make_conninfo(url, options=f"-c search_path={schema}")
    finally:
        with psycopg.connect(url, autocommit=True) as connection:
            connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


@pytest.fixture
def app(postgres_test_url):
    application = create_app(
        {"TESTING": True, "DATABASE_URL": postgres_test_url, "COMMIT_SHA": "integration-commit"}
    )
    with application.app_context():
        init_db()
        from app.db import get_db

        get_db().execute("TRUNCATE TABLE tasks RESTART IDENTITY")
    yield application


@pytest.fixture
def client(app):
    return app.test_client()
