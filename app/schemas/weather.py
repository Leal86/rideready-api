from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


AssessmentLevel = Literal[
    "FAVORABLE",
    "CAUTION",
    "UNFAVORABLE",
]


class WeatherAssessmentResponse(BaseModel):
    level: AssessmentLevel
    reasons: list[str]


class WeatherResponse(BaseModel):
    available: bool
    message: str | None = None
    available_from: date | None = None
    checked_at: datetime | None = None
    temperature: float | None = None
    apparent_temperature: float | None = None
    precipitation_probability: int | None = None
    precipitation: float | None = None
    weather_code: int | None = None
    wind_speed: float | None = None
    wind_gusts: float | None = None
    assessment: WeatherAssessmentResponse | None = None