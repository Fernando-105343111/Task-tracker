"""Request-scoped PostgreSQL connections and explicit schema initialisation."""

from pathlib import Path

import click
import psycopg
from flask import current_app, g
from flask.cli import with_appcontext
from psycopg.rows import dict_row


def get_db():
    if "db" not in g:
        g.db = psycopg.connect(
            current_app.config["DATABASE_URL"],
            autocommit=True,
            connect_timeout=3,
            row_factory=dict_row,
        )
    return g.db


def close_db(_error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_db():
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    get_db().execute(schema)


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Create the initial task table without deleting existing records."""
    init_db()
    click.echo("Task database initialised.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
