import httpx2

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.activity import ActivityCreate, ActivityResponse, ActivityUpdate
from app.services import activity as activity_service
from app.services.geocoding import geocode_location
from app.schemas.weather import WeatherResponse
from app.services.weather import get_weather_forecast
from datetime import timedelta

router = APIRouter(
    prefix="/activities",
    tags=["Activities"],
)


@router.get(
    "",
    response_model=list[ActivityResponse],
)
def list_activities(
    db: Session = Depends(get_db),
):
    return activity_service.list_activities(db)


@router.get(
    "/{activity_id}",
    response_model=ActivityResponse,
)
def get_activity(
    activity_id: int,
    db: Session = Depends(get_db),
):
    activity = activity_service.get_activity(db, activity_id)

    if activity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Atividade não encontrada.",
        )

    return activity


@router.post(
    "",
    response_model=ActivityResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_activity(
    payload: ActivityCreate,
    allow_conflict: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    if not allow_conflict:
        conflicting_activity = activity_service.get_activity_by_schedule(
            db,
            payload.scheduled_date,
            payload.scheduled_time,
        )

        if conflicting_activity is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": (
                        "Já existe uma atividade marcada " "para esta data e hora."
                    ),
                    "conflicting_activity_id": conflicting_activity.id,
                    "conflicting_activity_title": conflicting_activity.title,
                },
            )
    try:
        location = geocode_location(payload.location_name)
    except httpx2.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de localização temporariamente indisponível.",
        )

    if location is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Não foi possível encontrar o local informado.",
        )

    data = payload.model_dump()

    data["location_name"] = location.name
    data["latitude"] = location.latitude
    data["longitude"] = location.longitude

    return activity_service.create_activity(db, data)


@router.patch(
    "/{activity_id}",
    response_model=ActivityResponse,
)
@router.patch("/{activity_id}", response_model=ActivityResponse)
def update_activity(
    activity_id: int,
    payload: ActivityUpdate,
    db: Session = Depends(get_db),
):
    activity = activity_service.get_activity(db, activity_id)

    if activity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Atividade não encontrada.",
        )

    data = payload.model_dump(exclude_unset=True)

    if "location_name" in data:
        try:
            location = geocode_location(data["location_name"])
        except httpx2.HTTPError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Serviço de localização temporariamente indisponível.",
            )

        if location is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Não foi possível encontrar o local informado.",
            )

        data["location_name"] = location.name
        data["latitude"] = location.latitude
        data["longitude"] = location.longitude

    return activity_service.update_activity(db, activity, data)


@router.get(
    "/{activity_id}/weather",
    response_model=WeatherResponse,
)
def get_activity_weather(
    activity_id: int,
    db: Session = Depends(get_db),
):
    activity = activity_service.get_activity(db, activity_id)

    if activity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Atividade não encontrada.",
        )

    try:
        weather = get_weather_forecast(
            latitude=float(activity.latitude),
            longitude=float(activity.longitude),
            scheduled_date=activity.scheduled_date,
            scheduled_time=activity.scheduled_time,
        )
    except httpx2.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço meteorológico temporariamente indisponível.",
        )

    if weather is None:
        available_from = activity.scheduled_date - timedelta(days=15)

        return WeatherResponse(
            available=False,
            message=(
                "A previsão meteorológica ainda não está disponível. "
                "Consulte novamente a partir da data indicada."
            ),
            available_from=available_from,
        )

    return WeatherResponse(
        available=True,
        temperature=weather.temperature,
        apparent_temperature=weather.apparent_temperature,
        precipitation_probability=weather.precipitation_probability,
        precipitation=weather.precipitation,
        weather_code=weather.weather_code,
        wind_speed=weather.wind_speed,
        wind_gusts=weather.wind_gusts,
    )


@router.delete(
    "/{activity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_activity(
    activity_id: int,
    db: Session = Depends(get_db),
):
    activity = activity_service.get_activity(db, activity_id)

    if activity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Atividade não encontrada.",
        )

    activity_service.delete_activity(db, activity)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
