from datetime import date, time

from app.services.weather import (
    FORECAST_URL,
    get_current_weather,
    get_weather_forecast,
)


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


def test_get_weather_forecast_returns_requested_hour(monkeypatch):
    """Extrai a previsão correspondente à hora planeada da atividade."""

    response_data = {
        "hourly": {
            "time": [
                "2026-09-20T09:00",
                "2026-09-20T10:00",
            ],
            "temperature_2m": [18.0, 20.5],
            "apparent_temperature": [17.5, 20.0],
            "precipitation_probability": [10, 25],
            "precipitation": [0.0, 0.2],
            "weather_code": [1, 2],
            "wind_speed_10m": [8.0, 12.5],
            "wind_gusts_10m": [15.0, 22.0],
        }
    }

    def fake_get(url, params, timeout):
        assert url == FORECAST_URL
        assert params["latitude"] == 38.7223
        assert params["longitude"] == -9.1393
        assert params["timezone"] == "auto"
        assert params["forecast_days"] == 16
        assert timeout == 10.0

        return FakeResponse(response_data)

    monkeypatch.setattr(
        "app.services.weather.httpx2.get",
        fake_get,
    )

    result = get_weather_forecast(
        latitude=38.7223,
        longitude=-9.1393,
        scheduled_date=date(2026, 9, 20),
        scheduled_time=time(10, 37),
    )

    assert result is not None
    assert result.temperature == 20.5
    assert result.apparent_temperature == 20.0
    assert result.precipitation_probability == 25
    assert result.precipitation == 0.2
    assert result.weather_code == 2
    assert result.wind_speed == 12.5
    assert result.wind_gusts == 22.0


def test_get_weather_forecast_returns_none_without_hourly(monkeypatch):
    """Devolve None quando o Open-Meteo não fornece dados horários."""

    monkeypatch.setattr(
        "app.services.weather.httpx2.get",
        lambda *args, **kwargs: FakeResponse({}),
    )

    result = get_weather_forecast(
        latitude=38.7223,
        longitude=-9.1393,
        scheduled_date=date(2026, 9, 20),
        scheduled_time=time(10, 0),
    )

    assert result is None


def test_get_weather_forecast_returns_none_when_hour_is_missing(
    monkeypatch,
):
    """Devolve None quando a data/hora pedida não existe na previsão."""

    response_data = {
        "hourly": {
            "time": ["2026-09-20T09:00"],
            "temperature_2m": [18.0],
            "apparent_temperature": [17.5],
            "precipitation_probability": [10],
            "precipitation": [0.0],
            "weather_code": [1],
            "wind_speed_10m": [8.0],
            "wind_gusts_10m": [15.0],
        }
    }

    monkeypatch.setattr(
        "app.services.weather.httpx2.get",
        lambda *args, **kwargs: FakeResponse(response_data),
    )

    result = get_weather_forecast(
        latitude=38.7223,
        longitude=-9.1393,
        scheduled_date=date(2026, 9, 20),
        scheduled_time=time(15, 0),
    )

    assert result is None


def test_get_current_weather_returns_current_conditions(monkeypatch):
    """Converte as condições atuais e associa a probabilidade horária."""

    response_data = {
        "current": {
            "time": "2026-09-17T12:30",
            "temperature_2m": 22.5,
            "apparent_temperature": 23.1,
            "precipitation": 0.0,
            "weather_code": 1,
            "wind_speed_10m": 9.5,
            "wind_gusts_10m": 18.0,
        },
        "hourly": {
            "time": [
                "2026-09-17T12:00",
                "2026-09-17T13:00",
            ],
            "precipitation_probability": [15, 20],
        },
    }

    def fake_get(url, params, timeout):
        assert url == FORECAST_URL
        assert params["latitude"] == 38.7223
        assert params["longitude"] == -9.1393
        assert params["forecast_days"] == 1
        assert params["timezone"] == "auto"
        assert timeout == 10.0

        return FakeResponse(response_data)

    monkeypatch.setattr(
        "app.services.weather.httpx2.get",
        fake_get,
    )

    result = get_current_weather(
        latitude=38.7223,
        longitude=-9.1393,
    )

    assert result is not None
    assert result.observed_at == "2026-09-17T12:30"
    assert result.temperature == 22.5
    assert result.apparent_temperature == 23.1
    assert result.precipitation_probability == 15
    assert result.precipitation == 0.0
    assert result.weather_code == 1
    assert result.wind_speed == 9.5
    assert result.wind_gusts == 18.0


def test_get_current_weather_returns_none_without_current(monkeypatch):
    """Devolve None quando as condições atuais não estão disponíveis."""

    monkeypatch.setattr(
        "app.services.weather.httpx2.get",
        lambda *args, **kwargs: FakeResponse({}),
    )

    result = get_current_weather(
        latitude=38.7223,
        longitude=-9.1393,
    )

    assert result is None


def test_get_current_weather_returns_none_without_observation_time(
    monkeypatch,
):
    """Devolve None quando a observação atual não possui horário."""

    response_data = {
        "current": {
            "temperature_2m": 22.5,
        }
    }

    monkeypatch.setattr(
        "app.services.weather.httpx2.get",
        lambda *args, **kwargs: FakeResponse(response_data),
    )

    result = get_current_weather(
        latitude=38.7223,
        longitude=-9.1393,
    )

    assert result is None


def test_get_current_weather_uses_zero_when_hour_is_missing(
    monkeypatch,
):
    """Usa probabilidade zero quando não encontra a hora observada."""

    response_data = {
        "current": {
            "time": "2026-09-17T12:30",
            "temperature_2m": 22.5,
            "apparent_temperature": 23.1,
            "precipitation": 0.0,
            "weather_code": 1,
            "wind_speed_10m": 9.5,
            "wind_gusts_10m": 18.0,
        },
        "hourly": {
            "time": ["2026-09-17T10:00"],
            "precipitation_probability": [40],
        },
    }

    monkeypatch.setattr(
        "app.services.weather.httpx2.get",
        lambda *args, **kwargs: FakeResponse(response_data),
    )

    result = get_current_weather(
        latitude=38.7223,
        longitude=-9.1393,
    )

    assert result is not None
    assert result.precipitation_probability == 0
