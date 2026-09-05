import httpx2

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.location import LocationSuggestionResponse
from app.services.locations import search_locations

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
