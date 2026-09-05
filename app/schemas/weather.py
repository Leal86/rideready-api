from datetime import date

from pydantic import BaseModel


class WeatherResponse(BaseModel):
    available: bool
    message: str | None = None
    available_from: date | None = None
    temperature: float | None = None
    apparent_temperature: float | None = None
    precipitation_probability: int | None = None
    precipitation: float | None = None
    weather_code: int | None = None
    wind_speed: float | None = None
    wind_gusts: float | None = None