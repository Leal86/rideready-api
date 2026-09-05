from pydantic import BaseModel


class LocationSuggestionResponse(BaseModel):
    name: str
    city: str | None = None
    state: str | None = None
    country: str
    country_code: str
    latitude: float
    longitude: float
    formatted: str