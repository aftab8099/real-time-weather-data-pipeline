
from datetime import datetime, timezone
from decimal import Decimal

from src.db import get_connection


def test_weather_upsert_updates_existing_observation():
    """Reloading the same city/timestamp should update, not duplicate."""
    test_time = datetime(2099, 1, 1, 12, 0, tzinfo=timezone.utc)

    with get_connection() as conn:
        with conn.cursor() as cursor:
            # Roll back all test changes when this connection closes
            # its transaction block.
            try:
                cursor.execute(
                    """
                    SELECT city_id
                    FROM dim_city
                    WHERE city_name = %s
                    """,
                    ("Delhi",),
                )
                row = cursor.fetchone()
                assert row is not None, "Delhi must exist in dim_city"
                city_id = row[0]

                def upsert_temperature(temperature):
                    cursor.execute(
                        """
                        INSERT INTO fact_weather_observation (
                            city_id, observed_at, temperature_c
                        )
                        VALUES (%s, %s, %s)
                        ON CONFLICT (city_id, observed_at)
                        DO UPDATE SET
                            temperature_c = EXCLUDED.temperature_c
                        """,
                        (city_id, test_time, Decimal(str(temperature))),
                    )

                upsert_temperature(20.0)
                upsert_temperature(25.0)

                cursor.execute(
                    """
                    SELECT COUNT(*), MAX(temperature_c)
                    FROM fact_weather_observation
                    WHERE city_id = %s AND observed_at = %s
                    """,
                    (city_id, test_time),
                )
                count, temperature = cursor.fetchone()

                assert count == 1, "UPSERT created a duplicate observation"
                assert temperature == Decimal("25.00"), (
                    "UPSERT did not update the existing temperature"
                )
            finally:
                conn.rollback()
