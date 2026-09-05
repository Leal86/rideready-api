import os
from dataclasses import dataclass

import httpx2

GEOAPIFY_AUTOCOMPLETE_URL = "https://api.geoapify.com/v1/geocode/autocomplete"


@dataclass
class LocationSuggestion:
    name: str
    city: str | None
    state: str | None
    country: str
    country_code: str
    latitude: float
    longitude: float
    formatted: str


def search_locations(query: str) -> list[LocationSuggestion]:
    api_key = os.getenv("GEOAPIFY_API_KEY")

    if not api_key:
        raise RuntimeError("GEOAPIFY_API_KEY não está configurada.")

    params = {
        "text": query,
        "format": "json",
        "limit": 5,
        "apiKey": api_key,
    }

    response = httpx2.get(
        GEOAPIFY_AUTOCOMPLETE_URL,
        params=params,
        timeout=10.0,
    )

    response.raise_for_status()

    data = response.json()
    results = data.get("results", [])

    suggestions = []

    for item in results:
        name = (
            item.get("name")
            or item.get("address_line1")
            or item.get("city")
            or item.get("town")
            or item.get("village")
            or query
        )

        city = (
            item.get("city")
            or item.get("town")
            or item.get("village")
            or item.get("municipality")
        )

        state = item.get("state")
        country = item.get("country", "")

        display_parts = []

        if name:
            display_parts.append(name)

        if city and city.lower() != name.lower():
            display_parts.append(city)

        if state:
            normalized_parts = [part.lower() for part in display_parts]

            if state.lower() not in normalized_parts:
                display_parts.append(state)

        if country:
            normalized_parts = [part.lower() for part in display_parts]

            if country.lower() not in normalized_parts:
                display_parts.append(country)

        formatted = ", ".join(display_parts)

        suggestions.append(
            LocationSuggestion(
                name=name,
                city=city,
                state=state,
                country=country,
                country_code=item.get(
                    "country_code",
                    "",
                ),
                latitude=item["lat"],
                longitude=item["lon"],
                formatted=formatted,
            )
        )

    unique_suggestions = []
    seen = set()

    for suggestion in suggestions:
        key = suggestion.formatted.lower()

        if key not in seen:
            seen.add(key)
            unique_suggestions.append(suggestion)

    return unique_suggestions
