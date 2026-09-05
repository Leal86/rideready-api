from dataclasses import dataclass
from datetime import date, time

import httpx2


FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


@dataclass
class WeatherResult:
    temperature: float
    apparent_temperature: float
    precipitation_probability: int
    precipitation: float
    weather_code: int
    wind_speed: float
    wind_gusts: float


def get_weather_forecast(
    latitude: float,
    longitude: float,
    scheduled_date: date,
    scheduled_time: time,
) -> WeatherResult | None:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": (
            "temperature_2m,"
            "apparent_temperature,"
            "precipitation_probability,"
            "precipitation,"
            "weather_code,"
            "wind_speed_10m,"
            "wind_gusts_10m"
        ),
        "timezone": "auto",
        "forecast_days": 16,
    }

    response = httpx2.get(
        FORECAST_URL,
        params=params,
        timeout=10.0,
    )

    response.raise_for_status()

    data = response.json()
    hourly = data.get("hourly")

    if not hourly:
        return None

    target_hour = scheduled_time.replace(
        minute=0,
        second=0,
        microsecond=0,
    )

    target_datetime = (
        f"{scheduled_date.isoformat()}T"
        f"{target_hour.strftime('%H:%M')}"
    )

    try:
        index = hourly["time"].index(target_datetime)
    except ValueError:
        return None

    return WeatherResult(
        temperature=hourly["temperature_2m"][index],
        apparent_temperature=hourly["apparent_temperature"][index],
        precipitation_probability=hourly[
            "precipitation_probability"
        ][index],
        precipitation=hourly["precipitation"][index],
        weather_code=hourly["weather_code"][index],
        wind_speed=hourly["wind_speed_10m"][index],
        wind_gusts=hourly["wind_gusts_10m"][index],
    )