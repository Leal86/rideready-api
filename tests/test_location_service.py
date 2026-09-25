import pytest

from app.services.locations import (
    GEOAPIFY_AUTOCOMPLETE_URL,
    GEOAPIFY_REVERSE_URL,
    reverse_location,
    search_locations,
)


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


def test_search_locations_formats_and_removes_duplicates(monkeypatch):
    """Converte resultados do Geoapify e remove locais formatados duplicados."""

    monkeypatch.setenv("GEOAPIFY_API_KEY", "test-key")

    response_data = {
        "results": [
            {
                "name": "Parque das Nações",
                "city": "Lisboa",
                "state": "Lisboa",
                "country": "Portugal",
                "country_code": "pt",
                "lat": 38.768,
                "lon": -9.095,
                "timezone": {
                    "name": "Europe/Lisbon",
                },
            },
            {
                "name": "Parque das Nações",
                "city": "Lisboa",
                "state": "Lisboa",
                "country": "Portugal",
                "country_code": "pt",
                "lat": 38.768,
                "lon": -9.095,
                "timezone": {
                    "name": "Europe/Lisbon",
                },
            },
        ]
    }

    def fake_get(url, params, timeout):
        assert url == GEOAPIFY_AUTOCOMPLETE_URL
        assert params == {
            "text": "Parque das Nações",
            "format": "json",
            "limit": 5,
            "apiKey": "test-key",
        }
        assert timeout == 10.0

        return FakeResponse(response_data)

    monkeypatch.setattr(
        "app.services.locations.httpx2.get",
        fake_get,
    )

    result = search_locations("Parque das Nações")

    assert len(result) == 1

    location = result[0]

    assert location.name == "Parque das Nações"
    assert location.city == "Lisboa"
    assert location.state == "Lisboa"
    assert location.country == "Portugal"
    assert location.country_code == "pt"
    assert location.latitude == 38.768
    assert location.longitude == -9.095
    assert location.formatted == ("Parque das Nações, Lisboa, Portugal")


def test_search_locations_uses_fallback_fields(monkeypatch):
    """Usa campos alternativos quando name e city não estão presentes."""

    monkeypatch.setenv("GEOAPIFY_API_KEY", "test-key")

    response_data = {
        "results": [
            {
                "address_line1": "Praça do Comércio",
                "town": "Lisboa",
                "country": "Portugal",
                "lat": 38.7078,
                "lon": -9.1366,
                "timezone": {
                    "name": "Europe/Lisbon",
                },
            }
        ]
    }

    monkeypatch.setattr(
        "app.services.locations.httpx2.get",
        lambda *args, **kwargs: FakeResponse(response_data),
    )

    result = search_locations("Praça")

    assert len(result) == 1
    assert result[0].name == "Praça do Comércio"
    assert result[0].city == "Lisboa"
    assert result[0].country_code == ""
    assert result[0].formatted == ("Praça do Comércio, Lisboa, Portugal")
    assert result[0].timezone == "Europe/Lisbon"


def test_search_locations_includes_distinct_state(monkeypatch):
    """Inclui o estado quando ele é diferente do nome e da cidade."""

    monkeypatch.setenv("GEOAPIFY_API_KEY", "test-key")

    response_data = {
        "results": [
            {
                "name": "Central Park",
                "city": "New York",
                "state": "New York State",
                "country": "United States",
                "country_code": "us",
                "lat": 40.7829,
                "lon": -73.9654,
                "timezone": {
                    "name": "America/New_York",
                },
            }
        ]
    }

    monkeypatch.setattr(
        "app.services.locations.httpx2.get",
        lambda *args, **kwargs: FakeResponse(response_data),
    )

    result = search_locations("Central Park")

    assert len(result) == 1
    assert result[0].formatted == (
        "Central Park, New York, New York State, United States"
    )
    assert result[0].timezone == "America/New_York"


def test_search_locations_ignores_result_without_timezone(monkeypatch):
    """Ignora resultados que não informam um timezone IANA."""

    monkeypatch.setenv("GEOAPIFY_API_KEY", "test-key")

    response_data = {
        "results": [
            {
                "name": "Local sem timezone",
                "city": "Lisboa",
                "country": "Portugal",
                "country_code": "pt",
                "lat": 38.7223,
                "lon": -9.1393,
            }
        ]
    }

    monkeypatch.setattr(
        "app.services.locations.httpx2.get",
        lambda *args, **kwargs: FakeResponse(response_data),
    )

    assert search_locations("Local sem timezone") == []


def test_search_locations_returns_empty_list(monkeypatch):
    """Devolve lista vazia quando o Geoapify não encontra resultados."""

    monkeypatch.setenv("GEOAPIFY_API_KEY", "test-key")

    monkeypatch.setattr(
        "app.services.locations.httpx2.get",
        lambda *args, **kwargs: FakeResponse({"results": []}),
    )

    assert search_locations("Local inexistente") == []


def test_search_locations_requires_api_key(monkeypatch):
    """Impede a pesquisa quando a chave do Geoapify não está configurada."""

    monkeypatch.delenv(
        "GEOAPIFY_API_KEY",
        raising=False,
    )

    with pytest.raises(
        RuntimeError,
        match="GEOAPIFY_API_KEY não está configurada",
    ):
        search_locations("Lisboa")


def test_reverse_location_formats_result(monkeypatch):
    """Converte a resposta de geocodificação reversa em localização formatada."""

    monkeypatch.setenv("GEOAPIFY_API_KEY", "test-key")

    response_data = {
        "results": [
            {
                "city": "Lisboa",
                "state": "Lisboa",
                "country": "Portugal",
                "timezone": {
                    "name": "Europe/Lisbon",
                },
            }
        ]
    }

    def fake_get(url, params, timeout):
        assert url == GEOAPIFY_REVERSE_URL
        assert params == {
            "lat": 38.7223,
            "lon": -9.1393,
            "format": "json",
            "lang": "pt",
            "apiKey": "test-key",
        }
        assert timeout == 10.0

        return FakeResponse(response_data)

    monkeypatch.setattr(
        "app.services.locations.httpx2.get",
        fake_get,
    )

    result = reverse_location(
        latitude=38.7223,
        longitude=-9.1393,
    )

    assert result is not None
    assert result.city == "Lisboa"
    assert result.state == "Lisboa"
    assert result.country == "Portugal"
    assert result.formatted == "Lisboa, Portugal"
    assert result.timezone == "Europe/Lisbon"


def test_reverse_location_includes_distinct_state(monkeypatch):
    """Inclui o estado quando ele é diferente da cidade."""

    monkeypatch.setenv("GEOAPIFY_API_KEY", "test-key")

    response_data = {
        "results": [
            {
                "city": "New York",
                "state": "New York State",
                "country": "United States",
                "timezone": {
                    "name": "America/New_York",
                },
            }
        ]
    }

    monkeypatch.setattr(
        "app.services.locations.httpx2.get",
        lambda *args, **kwargs: FakeResponse(response_data),
    )

    result = reverse_location(
        latitude=40.7128,
        longitude=-74.0060,
    )

    assert result is not None
    assert result.city == "New York"
    assert result.state == "New York State"
    assert result.country == "United States"
    assert result.formatted == ("New York, New York State, United States")
    assert result.timezone == "America/New_York"


def test_reverse_location_returns_none_without_timezone(monkeypatch):
    """Devolve None quando o resultado não informa um timezone IANA."""

    monkeypatch.setenv("GEOAPIFY_API_KEY", "test-key")

    response_data = {
        "results": [
            {
                "city": "Lisboa",
                "state": "Lisboa",
                "country": "Portugal",
            }
        ]
    }

    monkeypatch.setattr(
        "app.services.locations.httpx2.get",
        lambda *args, **kwargs: FakeResponse(response_data),
    )

    result = reverse_location(
        latitude=38.7223,
        longitude=-9.1393,
    )

    assert result is None


def test_reverse_location_returns_none_without_results(monkeypatch):
    """Devolve None quando nenhuma localização é identificada."""

    monkeypatch.setenv("GEOAPIFY_API_KEY", "test-key")

    monkeypatch.setattr(
        "app.services.locations.httpx2.get",
        lambda *args, **kwargs: FakeResponse({"results": []}),
    )

    result = reverse_location(
        latitude=38.7223,
        longitude=-9.1393,
    )

    assert result is None


def test_reverse_location_requires_api_key(monkeypatch):
    """Impede a consulta quando a chave do Geoapify não está configurada."""

    monkeypatch.delenv(
        "GEOAPIFY_API_KEY",
        raising=False,
    )

    with pytest.raises(
        RuntimeError,
        match="GEOAPIFY_API_KEY não está configurada",
    ):
        reverse_location(
            latitude=38.7223,
            longitude=-9.1393,
        )
