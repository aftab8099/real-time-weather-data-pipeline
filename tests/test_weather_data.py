
from src.db import get_connection


def test_no_null_weather_temperatures():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*)
                FROM fact_weather_observation
                WHERE temperature_c IS NULL
            """)
            null_count = cursor.fetchone()[0]

    assert null_count == 0, "Some observations have missing temperatures"


def test_weather_humidity_is_valid():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*)
                FROM fact_weather_observation
                WHERE humidity_pct IS NOT NULL
                  AND (humidity_pct < 0 OR humidity_pct > 100)
            """)
            invalid_count = cursor.fetchone()[0]

    assert invalid_count == 0, "Humidity must be between 0 and 100"


def test_daily_mart_has_five_cities():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(DISTINCT city_id)
                FROM mart_daily_weather
            """)
            city_count = cursor.fetchone()[0]

    assert city_count == 5, f"Expected 5 cities, found {city_count}"


def test_daily_observation_counts_are_positive():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*)
                FROM mart_daily_weather
                WHERE observation_count <= 0
            """)
            invalid_count = cursor.fetchone()[0]

    assert invalid_count == 0, "Daily observation counts must be positive"
