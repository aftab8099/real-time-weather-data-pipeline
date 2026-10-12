
import pytest
import requests

from src.ingestion.weather_api import fetch_weather


COORDINATES = {"latitude": 28.6139, "longitude": 77.2090}


class FakeSession:
    """Mock session that supports a context manager."""

    def __init__(self, response):
        self.response = response

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def get(self, *args, **kwargs):
        return self.response


class FakeResponse:
    def __init__(self, data=None, error=None):
        self.data = data
        self.error = error

    def raise_for_status(self):
        if self.error:
            raise self.error

    def json(self):
        return self.data


def test_fetch_weather_returns_expected_structure(monkeypatch):
    response = FakeResponse(
        data={
            "timezone": "Asia/Kolkata",
            "current": {
                "time": "2026-10-13T10:00",
                "temperature_2m": 28.5,
                "relative_humidity_2m": 65,
                "precipitation": 0.0,
                "wind_speed_10m": 5.2,
                "weather_code": 1,
            },
        }
    )

    monkeypatch.setattr(
        "src.ingestion.weather_api.create_session",
        lambda: FakeSession(response),
    )

    result = fetch_weather("Delhi", COORDINATES)

    assert result["city"] == "Delhi"
    assert "retrieved_at" in result
    assert result["payload"]["current"]["temperature_2m"] == 28.5


def test_fetch_weather_raises_on_http_error(monkeypatch):
    response = FakeResponse(error=requests.HTTPError("API unavailable"))

    monkeypatch.setattr(
        "src.ingestion.weather_api.create_session",
        lambda: FakeSession(response),
    )

    with pytest.raises(requests.HTTPError):
        fetch_weather("Delhi", COORDINATES)


def test_fetch_weather_rejects_missing_current_data(monkeypatch):
    response = FakeResponse(data={"timezone": "Asia/Kolkata"})

    monkeypatch.setattr(
        "src.ingestion.weather_api.create_session",
        lambda: FakeSession(response),
    )

    with pytest.raises((ValueError, KeyError)):
        fetch_weather("Delhi", COORDINATES)
