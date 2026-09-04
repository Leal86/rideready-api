from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


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
        "/activities",
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "Caminhada de Teste"
    assert data["activity_type"] == "WALKING"
    assert data["location_name"] == "Lisboa"
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
        "/activities",
        json=payload,
    )

    activity_id = create_response.json()["id"]

    response = client.get(f"/activities/{activity_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == activity_id
    assert data["title"] == "Corrida de Teste"
    assert data["activity_type"] == "RUNNING"
    assert data["location_name"] == "Porto"


def test_get_activity_not_found():
    response = client.get("/activities/999999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Atividade não encontrada."
    }
    
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
        "/activities",
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
    assert data["location_name"] == "Sintra"

def test_update_activity_not_found():
    response = client.patch(
        "/activities/999999",
        json={
            "status": "COMPLETED",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Atividade não encontrada."
    }

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
        "/activities",
        json=payload,
    )

    activity_id = create_response.json()["id"]

    response = client.delete(
        f"/activities/{activity_id}"
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/activities/{activity_id}"
    )

    assert get_response.status_code == 404
    
def test_delete_activity_not_found():
    response = client.delete(
        "/activities/999999"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Atividade não encontrada."
    }

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