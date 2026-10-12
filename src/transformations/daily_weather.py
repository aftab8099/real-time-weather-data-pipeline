
import logging

from src.db import get_connection

logger = logging.getLogger(__name__)

DAILY_WEATHER_SQL = """
INSERT INTO mart_daily_weather (
    city_id,
    weather_date,
    avg_temperature_c,
    min_temperature_c,
    max_temperature_c,
    avg_humidity_pct,
    total_precipitation_mm,
    observation_count
)
SELECT
    city_id,
    (observed_at AT TIME ZONE 'Asia/Kolkata')::date,
    ROUND(AVG(temperature_c), 2),
    ROUND(MIN(temperature_c), 2),
    ROUND(MAX(temperature_c), 2),
    ROUND(AVG(humidity_pct), 2),
    ROUND(SUM(precipitation_mm), 2),
    COUNT(*)::integer
FROM fact_weather_observation
GROUP BY
    city_id,
    (observed_at AT TIME ZONE 'Asia/Kolkata')::date
ON CONFLICT (city_id, weather_date)
DO UPDATE SET
    avg_temperature_c = EXCLUDED.avg_temperature_c,
    min_temperature_c = EXCLUDED.min_temperature_c,
    max_temperature_c = EXCLUDED.max_temperature_c,
    avg_humidity_pct = EXCLUDED.avg_humidity_pct,
    total_precipitation_mm = EXCLUDED.total_precipitation_mm,
    observation_count = EXCLUDED.observation_count;
"""


def refresh_daily_weather() -> int:
    """Refresh daily summaries from the fact table."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(DAILY_WEATHER_SQL)
            rows_affected = cursor.rowcount

    logger.info(
        "Daily weather mart refreshed. Rows inserted/updated: %s",
        rows_affected,
    )
    return rows_affected


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    try:
        count = refresh_daily_weather()
        print(f"Daily weather transformation completed. Rows affected: {count}")
    except Exception:
        logger.exception("Daily weather transformation failed.")
        raise SystemExit(1)
