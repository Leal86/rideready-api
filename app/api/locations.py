import httpx2

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.location import (
    LocationSuggestionResponse,
    ReverseLocationResponse,
)
from app.services.locations import (
    reverse_location,
    search_locations,
)

router = APIRouter(
    prefix="/locations",
    tags=["Locations"],
)


@router.get(
    "/search",
    response_model=list[LocationSuggestionResponse],
)
def search_location_suggestions(
    q: str = Query(min_length=2, max_length=100),
):
    try:
        return search_locations(q)
    except httpx2.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de pesquisa de locais temporariamente indisponível.",
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de pesquisa de locais não está configurado.",
        )


@router.get(
    "/reverse",
    response_model=ReverseLocationResponse,
)
def get_reverse_location(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    try:
        location = reverse_location(
            latitude=latitude,
            longitude=longitude,
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Não foi possível identificar a localização.",
        )

    return location
