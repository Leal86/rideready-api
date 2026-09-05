import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.locations import LocationSuggestion
from app.services.weather import WeatherResult

client = TestClient(app)


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
        "status": "COMPLETED",
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
    assert data["status"] == "COMPLETED"
    assert data["notes"] == "Depois da atualização"

    assert data["activity_type"] == "HIKING"
    assert data["location_name"] == "Sintra, Portugal"


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

    assert data["available"] is True
    assert data["temperature"] == 23.6
    assert data["apparent_temperature"] == 26.7
    assert data["precipitation_probability"] == 0
    assert data["precipitation"] == 0.0
    assert data["weather_code"] == 0
    assert data["wind_speed"] == 2.9
    assert data["wind_gusts"] == 6.5


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

    assert data["available"] is False
    assert data["available_from"] == "2026-10-05"
    assert data["temperature"] is None
    assert data["wind_speed"] is None


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
