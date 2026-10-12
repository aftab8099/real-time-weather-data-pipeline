
from contextlib import contextmanager

import psycopg2

from src.config import get_database_config


@contextmanager
def get_connection():
    """Open a connection and always close it."""
    conn = psycopg2.connect(**get_database_config())

    try:
        with conn:
            yield conn
    finally:
        conn.close()


def check_connection() -> dict:
    """Verify PostgreSQL connectivity."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT current_database(), current_user, version()"
            )
            database, user, version = cursor.fetchone()

    return {
        "database": database,
        "user": user,
        "version": version,
    }
