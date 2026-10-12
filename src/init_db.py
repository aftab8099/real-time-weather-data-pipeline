
from pathlib import Path

from src.db import get_connection, check_connection

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_FILE = PROJECT_ROOT / "sql" / "schema.sql"


def initialize_database() -> None:
    """Create the project tables and seed the city dimension."""
    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(
            f"Schema file not found: {SCHEMA_FILE}"
        )

    schema_sql = SCHEMA_FILE.read_text(encoding="utf-8")

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(schema_sql)

    print("Database schema created successfully.")


if __name__ == "__main__":
    try:
        initialize_database()

        details = check_connection()
        print(f"Database: {details['database']}")
        print(f"User: {details['user']}")
        print("PostgreSQL connection verified.")
    except Exception:
        print("Database initialization failed.")
        raise
