from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import AirportIndexDep, LegacyDep
from app.schemas.api import FlightSearchRequest, FlightSearchResponse
from app.services.transform_search import transform_search_response

router = APIRouter(prefix="/flights", tags=["flights"])


@router.post("/search", response_model=FlightSearchResponse)
async def search_flights(
    body: FlightSearchRequest,
    legacy: LegacyDep,
    airports: AirportIndexDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    simulate_issues: bool = Query(False, description="Forward to legacy API to simulate latency, 503, and 429"),
) -> FlightSearchResponse:
    payload = body.model_dump(exclude_none=True)
    raw = await legacy.flight_search(payload, simulate_issues)
    if not isinstance(raw, dict):
        raw = {}
    city_map = await airports.city_map(legacy, simulate_issues)
    items = transform_search_response(raw, city_map)
    total = len(items)
    start = (page - 1) * page_size
    page_items = items[start : start + page_size]
    search_id = page_items[0].search_id if page_items else None
    if search_id is None and items:
        search_id = items[0].search_id
    return FlightSearchResponse(
        search_id=search_id,
        items=page_items,
        page=page,
        page_size=page_size,
        total=total,
    )
