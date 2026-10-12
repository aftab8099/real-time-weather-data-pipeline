
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / ".env")


def get_database_config() -> dict:
    """Load PostgreSQL settings from environment variables."""
    required_vars = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    ]

    missing = [
        key for key in required_vars
        if not os.getenv(key)
    ]

    if missing:
        raise ValueError(
            "Missing database configuration: "
            + ", ".join(missing)
        )

    try:
        port = int(os.environ["DB_PORT"])
    except ValueError as exc:
        raise ValueError("DB_PORT must be an integer") from exc

    return {
        "host": os.environ["DB_HOST"],
        "port": port,
        "dbname": os.environ["DB_NAME"],
        "user": os.environ["DB_USER"],
        "password": os.environ["DB_PASSWORD"],
        "connect_timeout": 5,
    }
