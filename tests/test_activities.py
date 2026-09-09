from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.locations import LocationSuggestion
from app.services.weather import WeatherResult

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_created_activities():

    before_response = client.get("/activities")
    existing_ids = {activity["id"] for activity in before_response.json()}

    yield

    after_response = client.get("/activities")

    for activity in after_response.json():
        if activity["id"] not in existing_ids:
            client.delete(f'/activities/{activity["id"]}')


@pytest.fixture(autouse=True)
def mock_location_search(monkeypatch):

    locations = {
        "Lisboa": LocationSuggestion(
            name="Lisboa",
            city="Lisboa",
            state="Lisboa",
            country="Portugal",
            country_code="pt",
            latitude=38.72509,
            longitude=-9.14980,
            formatted="Lisboa, Portugal",
        ),
        "Porto": LocationSuggestion(
            name="Porto",
            city="Porto",
            state="Porto",
            country="Portugal",
            country_code="pt",
            latitude=41.14850,
            longitude=-8.61097,
            formatted="Porto, Portugal",
        ),
        "Sintra": LocationSuggestion(
            name="Sintra",
            city="Sintra",
            state="Lisboa",
            country="Portugal",
            country_code="pt",
            latitude=38.80290,
            longitude=-9.38170,
            formatted="Sintra, Portugal",
        ),
        "Cascais": LocationSuggestion(
            name="Cascais",
            city="Cascais",
            state="Lisboa",
            country="Portugal",
            country_code="pt",
            latitude=38.69790,
            longitude=-9.42150,
            formatted="Cascais, Portugal",
        ),
    }

    def fake_search_locations(location_name):

        location = locations.get(location_name)

        if location is None:
            return []

        return [location]

    monkeypatch.setattr(
        "app.api.activities.search_locations",
        fake_search_locations,
    )


def test_list_activities():

    response = client.get("/activities")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_activity():

    payload = {
        "title": "Caminhada de Teste",
        "activity_type": "WALKING",
        "location_name": "Lisboa",
        "scheduled_date": "2026-09-10",
        "scheduled_time": "10:00:00",
        "notes": "Criada pelo pytest",
    }

    response = client.post(
        "/activities?allow_conflict=true",
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "Caminhada de Teste"
    assert data["activity_type"] == "WALKING"
    assert data["location_name"] == "Lisboa, Portugal"
    assert data["status"] == "PLANNED"
    assert "id" in data


def test_get_activity_by_id():

    payload = {
        "title": "Corrida de Teste",
        "activity_type": "RUNNING",
        "location_name": "Porto",
        "scheduled_date": "2026-09-11",
        "scheduled_time": "09:00:00",
        "notes": "Teste de consulta por ID",
    }

    create_response = client.post(
        "/activities?allow_conflict=true",
        json=payload,
    )

    activity_id = create_response.json()["id"]

    response = client.get(f"/activities/{activity_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == activity_id
    assert data["title"] == "Corrida de Teste"
    assert data["activity_type"] == "RUNNING"
    assert data["location_name"] == "Porto, Portugal"


def test_get_activity_not_found():

    response = client.get("/activities/999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Atividade não encontrada."}


def test_update_activity():

    payload = {
        "title": "Atividade para Atualizar",
        "activity_type": "HIKING",
        "location_name": "Sintra",
        "scheduled_date": "2026-09-12",
        "scheduled_time": "08:30:00",
        "notes": "Antes da atualização",
    }

    create_response = client.post(
        "/activities?allow_conflict=true",
        json=payload,
    )

    activity_id = create_response.json()["id"]

    update_payload = {
        "title": "Atividade Atualizada",
        "status": "CANCELLED",
        "notes": "Depois da atualização",
    }

    response = client.patch(
        f"/activities/{activity_id}",
        json=update_payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == activity_id
    assert data["title"] == "Atividade Atualizada"
    assert data["status"] == "CANCELLED"
    assert data["notes"] == "Depois da atualização"

    assert data["activity_type"] == "HIKING"
    assert data["location_name"] == "Sintra, Portugal"


def test_cannot_complete_future_activity():

    payload = {
        "title": "Atividade Futura",
        "activity_type": "WALKING",
        "location_name": "Lisboa",
        "scheduled_date": "2026-11-20",
        "scheduled_time": "10:00:00",
        "notes": "Teste de conclusão antecipada",
    }

    create_response = client.post(
        "/activities?allow_conflict=true",
        json=payload,
    )

    assert create_response.status_code == 201

    activity_id = create_response.json()["id"]

    response = client.patch(
        f"/activities/{activity_id}",
        json={
            "status": "COMPLETED",
        },
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": {
            "field": "status",
            "message": (
                "A atividade só pode ser concluída "
                "a partir da data e hora agendadas."
            ),
        }
    }


def test_can_complete_activity_when_same_patch_moves_it_to_past():
    """Confirma que o PATCH usa a nova data ao validar a conclusão."""

    payload = {
        "title": "Atividade para Conclusão",
        "activity_type": "WALKING",
        "location_name": "Lisboa",
        "scheduled_date": "2026-09-12",
        "scheduled_time": "13:00:00",
        "notes": "Teste de alteração de data e estado",
    }

    create_response = client.post(
        "/activities?allow_conflict=true",
        json=payload,
    )

    assert create_response.status_code == 201

    activity_id = create_response.json()["id"]

    update_response = client.patch(
        f"/activities/{activity_id}",
        json={
            "scheduled_date": "2026-09-08",
            "status": "COMPLETED",
        },
    )

    assert update_response.status_code == 200

    activity = update_response.json()

    assert activity["scheduled_date"] == "2026-09-08"
    assert activity["status"] == "COMPLETED"


def test_update_activity_not_found():

    response = client.patch(
        "/activities/999999",
        json={
            "status": "COMPLETED",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Atividade não encontrada."}


def test_delete_activity():

    payload = {
        "title": "Atividade para Eliminar",
        "activity_type": "CYCLING",
        "location_name": "Cascais",
        "scheduled_date": "2026-09-13",
        "scheduled_time": "11:00:00",
        "notes": "Será eliminada pelo teste",
    }

    create_response = client.post(
        "/activities?allow_conflict=true",
        json=payload,
    )

    activity_id = create_response.json()["id"]

    response = client.delete(f"/activities/{activity_id}")

    assert response.status_code == 204

    get_response = client.get(f"/activities/{activity_id}")

    assert get_response.status_code == 404


def test_delete_activity_not_found():

    response = client.delete("/activities/999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Atividade não encontrada."}


def test_create_activity_invalid_payload():

    payload = {
        "title": "A",
        "activity_type": "SWIMMING",
        "location_name": "Lisboa",
        "scheduled_date": "2026-09-10",
        "scheduled_time": "10:00:00",
    }

    response = client.post(
        "/activities",
        json=payload,
    )

    assert response.status_code == 422


def test_get_activity_weather_available(monkeypatch):

    payload = {
        "title": "Caminhada com Previsão",
        "activity_type": "WALKING",
        "location_name": "Lisboa",
        "scheduled_date": "2026-09-12",
        "scheduled_time": "09:30:00",
        "notes": "Teste de previsão disponível",
    }

    create_response = client.post(
        "/activities?allow_conflict=true",
        json=payload,
    )

    activity_id = create_response.json()["id"]

    def fake_weather_forecast(
        latitude,
        longitude,
        scheduled_date,
        scheduled_time,
    ):

        return WeatherResult(
            temperature=23.6,
            apparent_temperature=26.7,
            precipitation_probability=0,
            precipitation=0.0,
            weather_code=0,
            wind_speed=2.9,
            wind_gusts=6.5,
        )

    monkeypatch.setattr(
        "app.api.activities.get_weather_forecast",
        fake_weather_forecast,
    )

    response = client.get(f"/activities/{activity_id}/weather")

    assert response.status_code == 200

    data = response.json()

    assert data["checked_at"] is not None
    assert data["available"] is True
    assert data["temperature"] == 23.6
    assert data["apparent_temperature"] == 26.7
    assert data["precipitation_probability"] == 0
    assert data["precipitation"] == 0.0
    assert data["weather_code"] == 0
    assert data["wind_speed"] == 2.9
    assert data["wind_gusts"] == 6.5
    assert data["assessment"]["level"] == "FAVORABLE"
    assert data["assessment"]["reasons"] == [
        "Nenhuma condição meteorológica relevante de atenção foi identificada."
    ]


def test_weather_query_persists_latest_snapshot(monkeypatch):
    """Confirma que a última previsão consultada fica persistida na atividade."""

    payload = {
        "title": "Caminhada com Snapshot",
        "activity_type": "WALKING",
        "location_name": "Lisboa",
        "scheduled_date": "2026-09-12",
        "scheduled_time": "10:00:00",
        "notes": "Teste de persistência meteorológica",
    }

    create_response = client.post(
        "/activities?allow_conflict=true",
        json=payload,
    )

    assert create_response.status_code == 201

    activity_id = create_response.json()["id"]

    def fake_weather_forecast(
        latitude,
        longitude,
        scheduled_date,
        scheduled_time,
    ):
        return WeatherResult(
            temperature=24.5,
            apparent_temperature=25.1,
            precipitation_probability=20,
            precipitation=0.0,
            weather_code=1,
            wind_speed=12.4,
            wind_gusts=18.7,
        )

    monkeypatch.setattr(
        "app.api.activities.get_weather_forecast",
        fake_weather_forecast,
    )

    weather_response = client.get(f"/activities/{activity_id}/weather")

    assert weather_response.status_code == 200

    checked_at = weather_response.json()["checked_at"]

    assert checked_at is not None

    activity_response = client.get(f"/activities/{activity_id}")

    assert activity_response.status_code == 200

    activity = activity_response.json()

    assert datetime.fromisoformat(
        activity["weather_checked_at"].replace("Z", "+00:00")
    ) == datetime.fromisoformat(checked_at)
    assert activity["weather_temperature"] == 24.5
    assert activity["weather_apparent_temperature"] == 25.1
    assert activity["weather_precipitation_probability"] == 20
    assert activity["weather_precipitation"] == 0.0
    assert activity["weather_code"] == 1
    assert activity["weather_wind_speed"] == 12.4
    assert activity["weather_wind_gusts"] == 18.7
    assert activity["weather_assessment_level"] == "FAVORABLE"
    assert activity["weather_assessment_reasons"] == [
        "Nenhuma condição meteorológica relevante de atenção foi identificada."
    ]


def test_new_weather_query_replaces_previous_snapshot(monkeypatch):
    """Confirma que uma nova previsão substitui o snapshot anterior."""

    payload = {
        "title": "Caminhada com Atualização Meteorológica",
        "activity_type": "WALKING",
        "location_name": "Lisboa",
        "scheduled_date": "2026-09-12",
        "scheduled_time": "11:00:00",
        "notes": "Teste de substituição do snapshot meteorológico",
    }

    create_response = client.post(
        "/activities?allow_conflict=true",
        json=payload,
    )

    assert create_response.status_code == 201

    activity_id = create_response.json()["id"]

    forecasts = [
        WeatherResult(
            temperature=23.0,
            apparent_temperature=23.5,
            precipitation_probability=10,
            precipitation=0.0,
            weather_code=0,
            wind_speed=5.0,
            wind_gusts=8.0,
        ),
        WeatherResult(
            temperature=35.0,
            apparent_temperature=36.0,
            precipitation_probability=90,
            precipitation=8.0,
            weather_code=95,
            wind_speed=50.0,
            wind_gusts=70.0,
        ),
    ]

    def fake_weather_forecast(
        latitude,
        longitude,
        scheduled_date,
        scheduled_time,
    ):
        return forecasts.pop(0)

    monkeypatch.setattr(
        "app.api.activities.get_weather_forecast",
        fake_weather_forecast,
    )

    first_response = client.get(f"/activities/{activity_id}/weather")

    assert first_response.status_code == 200

    first_weather = first_response.json()

    assert first_weather["temperature"] == 23.0
    assert first_weather["assessment"]["level"] == "FAVORABLE"

    second_response = client.get(f"/activities/{activity_id}/weather")

    assert second_response.status_code == 200

    second_weather = second_response.json()

    assert second_weather["temperature"] == 35.0
    assert second_weather["apparent_temperature"] == 36.0
    assert second_weather["assessment"]["level"] == "UNFAVORABLE"

    activity_response = client.get(f"/activities/{activity_id}")

    assert activity_response.status_code == 200

    activity = activity_response.json()

    assert activity["weather_temperature"] == 35.0
    assert activity["weather_apparent_temperature"] == 36.0
    assert activity["weather_precipitation_probability"] == 90
    assert activity["weather_precipitation"] == 8.0
    assert activity["weather_code"] == 95
    assert activity["weather_wind_speed"] == 50.0
    assert activity["weather_wind_gusts"] == 70.0
    assert activity["weather_assessment_level"] == "UNFAVORABLE"

    assert datetime.fromisoformat(
        activity["weather_checked_at"].replace("Z", "+00:00")
    ) == datetime.fromisoformat(second_weather["checked_at"])

    assert activity["weather_temperature"] != first_weather["temperature"]


def test_activity_change_invalidates_weather_snapshot(monkeypatch):
    """Confirma que alterações relevantes invalidam a previsão armazenada."""

    payload = {
        "title": "Caminhada para Editar",
        "activity_type": "WALKING",
        "location_name": "Lisboa",
        "scheduled_date": "2026-09-12",
        "scheduled_time": "12:00:00",
        "notes": "Teste de invalidação do snapshot",
    }

    create_response = client.post(
        "/activities?allow_conflict=true",
        json=payload,
    )

    assert create_response.status_code == 201

    activity_id = create_response.json()["id"]

    def fake_weather_forecast(
        latitude,
        longitude,
        scheduled_date,
        scheduled_time,
    ):
        return WeatherResult(
            temperature=24.0,
            apparent_temperature=25.0,
            precipitation_probability=10,
            precipitation=0.0,
            weather_code=0,
            wind_speed=8.0,
            wind_gusts=12.0,
        )

    monkeypatch.setattr(
        "app.api.activities.get_weather_forecast",
        fake_weather_forecast,
    )

    weather_response = client.get(f"/activities/{activity_id}/weather")

    assert weather_response.status_code == 200

    before_update = client.get(f"/activities/{activity_id}").json()

    assert before_update["weather_checked_at"] is not None
    assert before_update["weather_temperature"] == 24.0

    update_response = client.patch(
        f"/activities/{activity_id}",
        json={
            "location_name": "Porto",
        },
    )

    assert update_response.status_code == 200

    activity = update_response.json()

    assert activity["location_name"] == "Porto, Portugal"

    assert activity["weather_checked_at"] is None
    assert activity["weather_temperature"] is None
    assert activity["weather_apparent_temperature"] is None
    assert activity["weather_precipitation_probability"] is None
    assert activity["weather_precipitation"] is None
    assert activity["weather_code"] is None
    assert activity["weather_wind_speed"] is None
    assert activity["weather_wind_gusts"] is None
    assert activity["weather_assessment_level"] is None
    assert activity["weather_assessment_reasons"] is None


def test_get_activity_weather_unavailable(monkeypatch):
    payload = {
        "title": "Caminhada Futura",
        "activity_type": "WALKING",
        "location_name": "Lisboa",
        "scheduled_date": "2026-10-20",
        "scheduled_time": "09:00:00",
        "notes": "Teste fora do horizonte",
    }

    create_response = client.post(
        "/activities?allow_conflict=true",
        json=payload,
    )

    activity_id = create_response.json()["id"]

    def fake_weather_forecast(
        latitude,
        longitude,
        scheduled_date,
        scheduled_time,
    ):
        return None

    monkeypatch.setattr(
        "app.api.activities.get_weather_forecast",
        fake_weather_forecast,
    )

    response = client.get(f"/activities/{activity_id}/weather")

    assert response.status_code == 200

    data = response.json()

    assert data["checked_at"] is None
    assert data["available"] is False
    assert data["available_from"] == "2026-10-05"
    assert data["temperature"] is None
    assert data["wind_speed"] is None
    assert data["assessment"] is None


def test_completed_activity_cannot_refresh_weather():
    """Confirma que uma atividade concluída não pode atualizar a previsão."""

    payload = {
        "title": "Caminhada Concluída",
        "activity_type": "WALKING",
        "location_name": "Lisboa",
        "scheduled_date": "2026-09-12",
        "scheduled_time": "13:00:00",
        "notes": "Teste de bloqueio meteorológico",
    }

    create_response = client.post(
        "/activities?allow_conflict=true",
        json=payload,
    )

    assert create_response.status_code == 201

    activity_id = create_response.json()["id"]

    date_update_response = client.patch(
        f"/activities/{activity_id}",
        json={
            "scheduled_date": "2026-09-08",
        },
    )

    assert date_update_response.status_code == 200

    status_update_response = client.patch(
        f"/activities/{activity_id}",
        json={
            "status": "COMPLETED",
        },
    )

    assert status_update_response.status_code == 200

    weather_response = client.get(f"/activities/{activity_id}/weather")

    assert weather_response.status_code == 409
    assert weather_response.json()["detail"] == (
        "A previsão meteorológica só pode ser atualizada " "para atividades planeadas."
    )


def test_cancelled_activity_cannot_refresh_weather():
    """Confirma que uma atividade cancelada não pode atualizar a previsão."""

    payload = {
        "title": "Caminhada Cancelada",
        "activity_type": "WALKING",
        "location_name": "Lisboa",
        "scheduled_date": "2026-09-12",
        "scheduled_time": "14:00:00",
        "notes": "Teste de bloqueio meteorológico",
    }

    create_response = client.post(
        "/activities?allow_conflict=true",
        json=payload,
    )

    assert create_response.status_code == 201

    activity_id = create_response.json()["id"]

    update_response = client.patch(
        f"/activities/{activity_id}",
        json={
            "status": "CANCELLED",
        },
    )

    assert update_response.status_code == 200

    weather_response = client.get(f"/activities/{activity_id}/weather")

    assert weather_response.status_code == 409
    assert weather_response.json()["detail"] == (
        "A previsão meteorológica só pode ser atualizada " "para atividades planeadas."
    )


def test_get_activity_weather_not_found():

    response = client.get("/activities/999999/weather")

    assert response.status_code == 404
    assert response.json() == {"detail": "Atividade não encontrada."}


def test_create_activity_schedule_conflict():

    payload = {
        "title": "Primeira Atividade no Horário",
        "activity_type": "WALKING",
        "location_name": "Lisboa",
        "scheduled_date": "2026-11-15",
        "scheduled_time": "15:30:00",
        "notes": "Teste de conflito de horário",
    }

    first_response = client.post(
        "/activities?allow_conflict=true",
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/activities",
        json={
            **payload,
            "title": "Segunda Atividade no Mesmo Horário",
        },
    )

    assert second_response.status_code == 409

    data = second_response.json()

    assert data["detail"]["message"] == (
        "Já existe uma atividade marcada para esta data e hora."
    )

    assert "conflicting_activity_id" in data["detail"]
    assert "conflicting_activity_title" in data["detail"]
