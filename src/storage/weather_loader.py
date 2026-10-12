
import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

from src.db import get_connection

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

logger = logging.getLogger(__name__)


def load_weather_file(file_path: Path, run_id: int) -> bool:
    """Load one raw weather response under the shared pipeline run."""
    with file_path.open("r", encoding="utf-8") as file:
        record = json.load(file)

    city_name = record["city"]
    retrieved_at = datetime.fromisoformat(record["retrieved_at"])
    payload = record["payload"]
    current = payload["current"]

    observed_at = datetime.fromisoformat(current["time"])

    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(
            tzinfo=ZoneInfo(payload.get("timezone", "Asia/Kolkata"))
        )

    temperature = current.get("temperature_2m")
    humidity = current.get("relative_humidity_2m")
    precipitation = current.get("precipitation")
    wind_speed = current.get("wind_speed_10m")
    weather_code = current.get("weather_code")

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT city_id FROM dim_city WHERE city_name = %s",
                (city_name,),
            )
            city_row = cursor.fetchone()

            if city_row is None:
                raise ValueError(f"Unknown city: {city_name}")

            city_id = city_row[0]

            cursor.execute(
                """
                INSERT INTO raw_api_responses
                    (run_id, city_id, retrieved_at, http_status, payload)
                VALUES (%s, %s, %s, %s, %s::jsonb)
                """,
                (run_id, city_id, retrieved_at, 200, json.dumps(payload)),
            )

            cursor.execute(
                """
                INSERT INTO fact_weather_observation (
                    city_id, observed_at, ingested_at,
                    temperature_c, humidity_pct,
                    precipitation_mm, wind_speed_kmh, weather_code
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (city_id, observed_at)
                DO UPDATE SET
                    ingested_at = EXCLUDED.ingested_at,
                    temperature_c = EXCLUDED.temperature_c,
                    humidity_pct = EXCLUDED.humidity_pct,
                    precipitation_mm = EXCLUDED.precipitation_mm,
                    wind_speed_kmh = EXCLUDED.wind_speed_kmh,
                    weather_code = EXCLUDED.weather_code
                """,
                (
                    city_id,
                    observed_at,
                    datetime.now(timezone.utc),
                    Decimal(str(temperature)) if temperature is not None else None,
                    Decimal(str(humidity)) if humidity is not None else None,
                    Decimal(str(precipitation)) if precipitation is not None else None,
                    Decimal(str(wind_speed)) if wind_speed is not None else None,
                    weather_code,
                ),
            )

    logger.info(
        "Loaded %s | run_id=%s | observation time=%s",
        city_name,
        run_id,
        observed_at.isoformat(),
    )
    return True


def main(files=None, run_id=None) -> tuple[int, int]:
    """Load files under an existing pipeline run and return success/failure counts."""
    if run_id is None:
        raise ValueError("run_id is required; create it in the pipeline first")

    files = sorted(files if files is not None else RAW_DIR.glob("*.json"))

    if not files:
        raise FileNotFoundError(f"No JSON files found in {RAW_DIR}")

    succeeded = 0
    failed = 0

    for file_path in files:
        try:
            load_weather_file(file_path, run_id)
            succeeded += 1
        except Exception:
            logger.exception("Failed to load %s", file_path.name)
            failed += 1

    logger.info(
        "Loading complete | run_id=%s | succeeded=%d | failed=%d",
        run_id,
        succeeded,
        failed,
    )

    return succeeded, failed


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    raise SystemExit(
        "Run the complete pipeline with: python -m src.pipeline"
    )
