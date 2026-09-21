from typing import Annotated

import httpx2
from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.weather import CurrentWeatherResponse
from app.services.weather import get_current_weather


router = APIRouter(
    prefix="/weather",
    tags=["Weather"],
)


@router.get(
    "/current",
    response_model=CurrentWeatherResponse,
)
def get_current_weather_conditions(
    latitude: Annotated[float, Query(ge=-90, le=90)],
    longitude: Annotated[float, Query(ge=-180, le=180)],
):
    try:
        weather = get_current_weather(
            latitude=latitude,
            longitude=longitude,
        )
    except httpx2.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço meteorológico temporariamente indisponível.",
        )

    if weather is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível obter as condições meteorológicas atuais.",
        )

    return CurrentWeatherResponse(
        observed_at=weather.observed_at,
        temperature=weather.temperature,
        apparent_temperature=weather.apparent_temperature,
        precipitation_probability=weather.precipitation_probability,
        precipitation=weather.precipitation,
        weather_code=weather.weather_code,
        wind_speed=weather.wind_speed,
        wind_gusts=weather.wind_gusts,
    )