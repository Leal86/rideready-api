from datetime import date, datetime, time
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ActivityType = Literal[
    "WALKING",
    "RUNNING",
    "CYCLING",
    "HIKING",
    "OTHER",
]

ActivityStatus = Literal[
    "PLANNED",
    "COMPLETED",
    "CANCELLED",
]


class ActivityBase(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    activity_type: ActivityType
    location_name: str = Field(min_length=2, max_length=150)
    scheduled_date: date
    scheduled_time: time
    notes: str | None = None


class ActivityCreate(ActivityBase):
    pass


class ActivityUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=120)
    activity_type: ActivityType | None = None
    location_name: str | None = Field(default=None, min_length=2, max_length=150)
    scheduled_date: date | None = None
    scheduled_time: time | None = None
    notes: str | None = None
    status: ActivityStatus | None = None


class ActivityResponse(ActivityBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    latitude: Decimal
    longitude: Decimal
    status: ActivityStatus
    created_at: datetime
    updated_at: datetime

    weather_checked_at: datetime | None = None
    weather_temperature: float | None = None
    weather_apparent_temperature: float | None = None
    weather_precipitation_probability: int | None = None
    weather_precipitation: float | None = None
    weather_code: int | None = None
    weather_wind_speed: float | None = None
    weather_wind_gusts: float | None = None
    weather_assessment_level: str | None = None
    weather_assessment_reasons: list[str] | None = None
