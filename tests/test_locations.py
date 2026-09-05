from fastapi.testclient import TestClient

from app.main import app
from app.services.locations import LocationSuggestion


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
    assert (
        data[0]["formatted"]
        == "Cais do Sodré, Lisbon, Portugal"
    )


def test_search_locations_query_too_short():
    response = client.get(
        "/locations/search",
        params={"q": "A"},
    )

    assert response.status_code == 422


def test_search_locations_not_configured(monkeypatch):
    def fake_search_locations(query):
        raise RuntimeError(
            "GEOAPIFY_API_KEY não está configurada."
        )

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