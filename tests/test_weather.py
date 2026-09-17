import httpx2
from fastapi.testclient import TestClient

from app.main import app
from app.services.weather import CurrentWeatherResult

client = TestClient(app)


def test_get_current_weather(monkeypatch):
    """Confirma que o endpoint devolve as condições meteorológicas atuais."""

    def fake_current_weather(latitude, longitude):
        assert latitude == 38.7223
        assert longitude == -9.1393

        return CurrentWeatherResult(
            observed_at="2026-09-15T09:30",
            temperature=21.5,
            apparent_temperature=22.2,
            precipitation_probability=0,
            precipitation=0.0,
            weather_code=1,
            wind_speed=8.4,
            wind_gusts=18.4,
        )

    monkeypatch.setattr(
        "app.api.weather.get_current_weather",
        fake_current_weather,
    )

    response = client.get(
        "/weather/current",
        params={
            "latitude": 38.7223,
            "longitude": -9.1393,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data == {
        "observed_at": "2026-09-15T09:30",
        "temperature": 21.5,
        "apparent_temperature": 22.2,
        "precipitation_probability": 0,
        "precipitation": 0.0,
        "weather_code": 1,
        "wind_speed": 8.4,
        "wind_gusts": 18.4,
    }


def test_get_current_weather_rejects_invalid_coordinates():
    """Confirma que latitude e longitude inválidas são rejeitadas."""

    response = client.get(
        "/weather/current",
        params={
            "latitude": 91,
            "longitude": -9.1393,
        },
    )

    assert response.status_code == 422

    response = client.get(
        "/weather/current",
        params={
            "latitude": 38.7223,
            "longitude": 181,
        },
    )

    assert response.status_code == 422


def test_get_current_weather_service_unavailable(monkeypatch):
    """Confirma o tratamento de falha do serviço meteorológico externo."""

    def fake_current_weather(latitude, longitude):
        raise httpx2.HTTPError("Serviço meteorológico indisponível")

    monkeypatch.setattr(
        "app.api.weather.get_current_weather",
        fake_current_weather,
    )

    response = client.get(
        "/weather/current",
        params={
            "latitude": 38.7223,
            "longitude": -9.1393,
        },
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Serviço meteorológico temporariamente indisponível."
    }
