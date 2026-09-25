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
from app.services.locations import reverse_location, search_locations
from app.schemas.weather import WeatherResponse
from app.services.weather import get_weather_forecast
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from app.services.assessment import assess_weather_conditions

router = APIRouter(
    prefix="/activities",
    tags=["Activities"],
)

ACTIVITY_NOT_FOUND = "Atividade não encontrada."


def get_scheduled_datetime(
    scheduled_date,
    scheduled_time,
    timezone_name: str,
) -> datetime:
    """Converte a data e hora locais da atividade num datetime com timezone."""
    return datetime.combine(
        scheduled_date,
        scheduled_time,
        tzinfo=ZoneInfo(timezone_name),
    )


def resolve_activity_timezone(
    activity,
) -> str:
    """Obtém o timezone da atividade, inclusive para registos antigos."""
    if activity.timezone:
        return activity.timezone

    try:
        location = reverse_location(
            latitude=float(activity.latitude),
            longitude=float(activity.longitude),
        )
    except httpx2.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de localização temporariamente indisponível.",
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de localização não está configurado.",
        )

    if location is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                "Não foi possível determinar o timezone " "da localização da atividade."
            ),
        )

    return location.timezone


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
            detail=ACTIVITY_NOT_FOUND,
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
    scheduled_datetime = datetime.combine(
        payload.scheduled_date,
        payload.scheduled_time,
    )

    if scheduled_datetime < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "field": "scheduled_datetime",
                "message": "A data e a hora da atividade não podem estar no passado.",
            },
        )

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
                    "message": "Já existe uma atividade marcada para esta data e hora.",
                    "conflicting_activity_id": conflicting_activity.id,
                    "conflicting_activity_title": conflicting_activity.title,
                },
            )
    try:
        locations = search_locations(payload.location_name)
    except httpx2.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de localização temporariamente indisponível.",
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de localização não está configurado.",
        )

    if not locations:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Não foi possível encontrar o local informado.",
        )

    location = locations[0]

    scheduled_datetime = get_scheduled_datetime(
        payload.scheduled_date,
        payload.scheduled_time,
        location.timezone,
    )

    if scheduled_datetime < datetime.now(ZoneInfo(location.timezone)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "field": "scheduled_datetime",
                "message": ("A data e a hora da atividade não podem estar no passado."),
            },
        )

    data = payload.model_dump()

    data["location_name"] = location.formatted
    data["latitude"] = location.latitude
    data["longitude"] = location.longitude
    data["timezone"] = location.timezone

    return activity_service.create_activity(db, data)


@router.patch(
    "/{activity_id}",
    response_model=ActivityResponse,
)
def update_activity(
    activity_id: int,
    payload: ActivityUpdate,
    db: Session = Depends(get_db),
):
    activity = activity_service.get_activity(db, activity_id)

    if activity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ACTIVITY_NOT_FOUND,
        )

    data = payload.model_dump(exclude_unset=True)

    weather_relevant_fields = {
        "location_name",
        "scheduled_date",
        "scheduled_time",
        "activity_type",
    }

    if weather_relevant_fields.intersection(data):
        data.update(
            {
                "weather_checked_at": None,
                "weather_temperature": None,
                "weather_apparent_temperature": None,
                "weather_precipitation_probability": None,
                "weather_precipitation": None,
                "weather_code": None,
                "weather_wind_speed": None,
                "weather_wind_gusts": None,
                "weather_assessment_level": None,
                "weather_assessment_reasons": None,
            }
        )

    # Se a localização foi alterada, obtemos novamente as coordenadas
    # e o timezone correspondentes ao novo local.
    if "location_name" in data:
        try:
            locations = search_locations(payload.location_name)
        except httpx2.HTTPError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Serviço de localização temporariamente indisponível.",
            )
        except RuntimeError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Serviço de localização não está configurado.",
            )

        if not locations:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Não foi possível encontrar o local informado.",
            )

        location = locations[0]

        data["location_name"] = location.formatted
        data["latitude"] = location.latitude
        data["longitude"] = location.longitude
        data["timezone"] = location.timezone

    # A validação de conclusão precisa usar o estado final da atividade:
    # data/hora recebidas no PATCH, quando existirem, e o timezone da
    # nova localização ou da atividade já armazenada.
    if data.get("status") == "COMPLETED":
        scheduled_date = data.get(
            "scheduled_date",
            activity.scheduled_date,
        )
        scheduled_time = data.get(
            "scheduled_time",
            activity.scheduled_time,
        )

        timezone_name = data.get("timezone")

        if timezone_name is None:
            timezone_name = resolve_activity_timezone(activity)

            if activity.timezone is None:
                data["timezone"] = timezone_name

        scheduled_datetime = get_scheduled_datetime(
            scheduled_date,
            scheduled_time,
            timezone_name,
        )

        if scheduled_datetime > datetime.now(ZoneInfo(timezone_name)):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "field": "status",
                    "message": (
                        "A atividade só pode ser concluída "
                        "a partir da data e hora agendadas."
                    ),
                },
            )

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
            detail=ACTIVITY_NOT_FOUND,
        )

    if activity.status != "PLANNED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A previsão meteorológica só pode ser atualizada "
                "para atividades planeadas."
            ),
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

    assessment = assess_weather_conditions(
        activity_type=activity.activity_type,
        apparent_temperature=weather.apparent_temperature,
        precipitation_probability=weather.precipitation_probability,
        precipitation=weather.precipitation,
        wind_speed=weather.wind_speed,
        wind_gusts=weather.wind_gusts,
    )

    checked_at = datetime.now().astimezone()

    snapshot_data = {
        "weather_checked_at": checked_at,
        "weather_temperature": weather.temperature,
        "weather_apparent_temperature": weather.apparent_temperature,
        "weather_precipitation_probability": (
            weather.precipitation_probability
        ),
        "weather_precipitation": weather.precipitation,
        "weather_code": weather.weather_code,
        "weather_wind_speed": weather.wind_speed,
        "weather_wind_gusts": weather.wind_gusts,
        "weather_assessment_level": assessment.level,
        "weather_assessment_reasons": assessment.reasons,
    }

    activity_service.update_activity(
        db,
        activity,
        snapshot_data,
    )

    return WeatherResponse(
        available=True,
        checked_at=checked_at,
        temperature=weather.temperature,
        apparent_temperature=weather.apparent_temperature,
        precipitation_probability=weather.precipitation_probability,
        precipitation=weather.precipitation,
        weather_code=weather.weather_code,
        wind_speed=weather.wind_speed,
        wind_gusts=weather.wind_gusts,
        assessment={
            "level": assessment.level,
            "reasons": assessment.reasons,
        },
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
            detail=ACTIVITY_NOT_FOUND,
        )

    activity_service.delete_activity(db, activity)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
