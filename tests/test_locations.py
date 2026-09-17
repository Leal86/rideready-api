import httpx2
from fastapi.testclient import TestClient

from app.main import app
from app.services.locations import (
    LocationSuggestion,
    ReverseLocation,
)

client = TestClient(app)


def test_search_locations(monkeypatch):
    def fake_search_locations(query):
        assert query == "Cais do Sodré"

        return [
            LocationSuggestion(
                name="Cais do Sodré",
                city="Lisbon",
                state=None,
                country="Portugal",
                country_code="pt",
                latitude=38.705681,
                longitude=-9.1435482,
                formatted="Cais do Sodré, Lisbon, Portugal",
            )
        ]

    monkeypatch.setattr(
        "app.api.locations.search_locations",
        fake_search_locations,
    )

    response = client.get(
        "/locations/search",
        params={"q": "Cais do Sodré"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Cais do Sodré"
    assert data[0]["country"] == "Portugal"
    assert data[0]["latitude"] == 38.705681
    assert data[0]["longitude"] == -9.1435482
    assert data[0]["formatted"] == "Cais do Sodré, Lisbon, Portugal"


def test_search_locations_query_too_short():
    response = client.get(
        "/locations/search",
        params={"q": "A"},
    )

    assert response.status_code == 422


def test_search_locations_not_configured(monkeypatch):
    def fake_search_locations(query):
        raise RuntimeError("GEOAPIFY_API_KEY não está configurada.")

    monkeypatch.setattr(
        "app.api.locations.search_locations",
        fake_search_locations,
    )

    response = client.get(
        "/locations/search",
        params={"q": "Lisboa"},
    )

    assert response.status_code == 503
    assert (
        response.json()["detail"]
        == "Serviço de pesquisa de locais não está configurado."
    )


def test_search_locations_service_unavailable(monkeypatch):
    """Retorna 503 quando o serviço externo de pesquisa de locais falha."""

    def fake_search_locations(query):
        raise httpx2.HTTPError("Geoapify indisponível")

    monkeypatch.setattr(
        "app.api.locations.search_locations",
        fake_search_locations,
    )

    response = client.get(
        "/locations/search",
        params={"q": "Lisboa"},
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Serviço de pesquisa de locais temporariamente indisponível."
    }


def test_reverse_location(monkeypatch):
    """Confirma que coordenadas válidas devolvem a localização formatada."""

    def fake_reverse_location(latitude, longitude):
        assert latitude == 38.7223
        assert longitude == -9.1393

        return ReverseLocation(
            city="Lisboa",
            state="Lisboa",
            country="Portugal",
            formatted="Lisboa, Portugal",
        )

    monkeypatch.setattr(
        "app.api.locations.reverse_location",
        fake_reverse_location,
    )

    response = client.get(
        "/locations/reverse",
        params={
            "latitude": 38.7223,
            "longitude": -9.1393,
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "city": "Lisboa",
        "state": "Lisboa",
        "country": "Portugal",
        "formatted": "Lisboa, Portugal",
    }


def test_reverse_location_rejects_invalid_coordinates():
    """Confirma que coordenadas fora dos limites são rejeitadas."""

    response = client.get(
        "/locations/reverse",
        params={
            "latitude": 91,
            "longitude": -9.1393,
        },
    )

    assert response.status_code == 422

    response = client.get(
        "/locations/reverse",
        params={
            "latitude": 38.7223,
            "longitude": 181,
        },
    )

    assert response.status_code == 422


def test_reverse_location_not_configured(monkeypatch):
    """Confirma o tratamento da ausência de configuração do Geoapify."""

    def fake_reverse_location(latitude, longitude):
        raise RuntimeError("GEOAPIFY_API_KEY não está configurada.")

    monkeypatch.setattr(
        "app.api.locations.reverse_location",
        fake_reverse_location,
    )

    response = client.get(
        "/locations/reverse",
        params={
            "latitude": 38.7223,
            "longitude": -9.1393,
        },
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Serviço de localização não está configurado."}


def test_reverse_location_service_unavailable(monkeypatch):
    """Confirma o tratamento de falha temporária do Geoapify."""

    def fake_reverse_location(latitude, longitude):
        raise httpx2.HTTPError("Serviço de localização indisponível")

    monkeypatch.setattr(
        "app.api.locations.reverse_location",
        fake_reverse_location,
    )

    response = client.get(
        "/locations/reverse",
        params={
            "latitude": 38.7223,
            "longitude": -9.1393,
        },
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Serviço de localização temporariamente indisponível."
    }


def test_reverse_location_not_found(monkeypatch):
    """Confirma o tratamento quando nenhuma localização é identificada."""

    def fake_reverse_location(latitude, longitude):
        return None

    monkeypatch.setattr(
        "app.api.locations.reverse_location",
        fake_reverse_location,
    )

    response = client.get(
        "/locations/reverse",
        params={
            "latitude": 38.7223,
            "longitude": -9.1393,
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Não foi possível identificar a localização."}
