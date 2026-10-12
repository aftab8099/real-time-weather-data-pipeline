
import logging
from pathlib import Path

from src.db import get_connection
from src.ingestion import weather_api
from src.storage import weather_loader
from src.transformations.daily_weather import refresh_daily_weather

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


def create_ingestion_run(cities_requested: int) -> int:
    """Create one tracking record for the complete pipeline execution."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO ingestion_runs
                    (status, cities_requested)
                VALUES ('running', %s)
                RETURNING run_id
                """,
                (cities_requested,),
            )
            return cursor.fetchone()[0]


def finish_ingestion_run(
    run_id: int,
    status: str,
    cities_succeeded: int,
    cities_failed: int,
    error_message: str | None = None,
) -> None:
    """Finalize run status and counts."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE ingestion_runs
                SET status = %s,
                    finished_at = NOW(),
                    cities_succeeded = %s,
                    cities_failed = %s,
                    error_message = %s
                WHERE run_id = %s
                """,
                (
                    status,
                    cities_succeeded,
                    cities_failed,
                    error_message[:2000] if error_message else None,
                    run_id,
                ),
            )


def run_pipeline() -> None:
    """Run ingestion, loading, and daily transformation."""
    logger.info("Starting weather data pipeline")

    existing_files = set(RAW_DIR.glob("*.json"))
    requested = len(weather_api.CITIES)
    run_id = create_ingestion_run(requested)

    succeeded = 0
    failed = 0
    run_finalized = False

    logger.info("Created ingestion run | run_id=%s", run_id)

    try:
        # Stage 1: Fetch fresh weather data.
        weather_api.main()

        new_files = sorted(set(RAW_DIR.glob("*.json")) - existing_files)

        if not new_files:
            raise RuntimeError(
                "Ingestion completed but created no new JSON files"
            )

        logger.info("Stage 1 complete | New files: %d", len(new_files))

        # Stage 2: Load data under the same run ID.
        succeeded, failed = weather_loader.main(new_files, run_id=run_id)

        if failed:
            status = "partial_failure" if succeeded else "failed"
            finish_ingestion_run(
                run_id, status, succeeded, failed,
                "One or more weather files failed to load",
            )
            run_finalized = True
            raise RuntimeError(
                f"Loading failed for {failed} file(s); daily mart not refreshed"
            )

        logger.info("Stage 2 complete | Weather data loaded")

        # Stage 3: Refresh daily summaries.
        rows_affected = refresh_daily_weather()
        logger.info(
            "Stage 3 complete | Daily mart rows inserted/updated: %d",
            rows_affected,
        )

        finish_ingestion_run(
            run_id, "success", succeeded, failed
        )
        run_finalized = True

        logger.info(
            "Weather pipeline completed successfully | run_id=%s",
            run_id,
        )

    except BaseException as exc:
        if not run_finalized:
            status = "partial_failure" if succeeded else "failed"
            try:
                finish_ingestion_run(
                    run_id,
                    status,
                    succeeded,
                    failed,
                    f"{type(exc).__name__}: {exc}",
                )
            except Exception:
                logger.exception(
                    "Could not finalize ingestion run %s", run_id
                )

        raise


if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception:
        logger.exception("Weather data pipeline failed")
        raise SystemExit(1)
