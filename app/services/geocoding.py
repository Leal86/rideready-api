from dataclasses import dataclass

import httpx2


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"


@dataclass
class GeocodingResult:
    name: str
    latitude: float
    longitude: float


def geocode_location(location_name: str) -> GeocodingResult | None:
    params = {
        "name": location_name,
        "count": 1,
        "language": "pt",
        "format": "json",
    }

    try:
        response = httpx2.get(
            GEOCODING_URL,
            params=params,
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx2.HTTPError:
        raise

    data = response.json()
    results = data.get("results")

    if not results:
        return None

    location = results[0]

    return GeocodingResult(
        name=location["name"],
        latitude=location["latitude"],
        longitude=location["longitude"],
    )