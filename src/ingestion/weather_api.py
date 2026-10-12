
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://api.open-meteo.com/v1/forecast"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

CITIES = {
    "Delhi": {"latitude": 28.6139, "longitude": 77.2090},
    "Mumbai": {"latitude": 19.0760, "longitude": 72.8777},
    "Bengaluru": {"latitude": 12.9716, "longitude": 77.5946},
    "Hyderabad": {"latitude": 17.3850, "longitude": 78.4867},
    "Chennai": {"latitude": 13.0827, "longitude": 80.2707},
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


def create_session() -> requests.Session:
    """Create an HTTP session with retries for temporary failures."""
    retry_strategy = Retry(
        total=3,
        connect=3,
        read=3,
        status=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True,
    )

    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)

    return session


def fetch_weather(city_name: str, coordinates: dict) -> dict:
    """Fetch current weather for one city."""
    params = {
        "latitude": coordinates["latitude"],
        "longitude": coordinates["longitude"],
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "precipitation,"
            "wind_speed_10m,"
            "weather_code"
        ),
        "timezone": "Asia/Kolkata",
    }

    with create_session() as session:
        response = session.get(
            BASE_URL,
            params=params,
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()

    if not isinstance(payload.get("current"), dict):
        raise ValueError(
            f"Invalid current weather response for {city_name}"
        )

    return {
        "city": city_name,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }


def save_raw_response(result: dict) -> Path:
    """Save the original API response as a JSON file."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    city_slug = result["city"].lower()
    output_file = RAW_DIR / f"{city_slug}_{timestamp}.json"

    output_file.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return output_file


def main() -> None:
    successful = 0
    failed = 0

    for city_name, coordinates in CITIES.items():
        try:
            result = fetch_weather(city_name, coordinates)
            output_file = save_raw_response(result)
            current = result["payload"]["current"]

            logger.info(
                "%s | Temperature: %s°C | Humidity: %s%% | "
                "Wind: %s km/h | Saved: %s",
                city_name,
                current.get("temperature_2m"),
                current.get("relative_humidity_2m"),
                current.get("wind_speed_10m"),
                output_file.name,
            )

            successful += 1

        except (requests.RequestException, ValueError, OSError) as exc:
            logger.error("%s failed: %s", city_name, exc)
            failed += 1

    logger.info(
        "Ingestion finished | successful=%s | failed=%s",
        successful,
        failed,
    )

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
