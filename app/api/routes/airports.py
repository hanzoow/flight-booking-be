from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import AirportIndexDep, LegacyDep
from app.schemas.api import AirportOut

router = APIRouter(prefix="/airports", tags=["airports"])


@router.get("", response_model=list[AirportOut])
async def list_airports(
    legacy: LegacyDep,
    airports: AirportIndexDep,
    simulate_issues: bool = Query(False),
) -> list[AirportOut]:
    return await airports.get_all(legacy, simulate_issues)


@router.get("/{code}", response_model=AirportOut)
async def get_airport(
    code: str,
    legacy: LegacyDep,
    simulate_issues: bool = Query(False),
) -> AirportOut:
    raw = await legacy.airport_one(code.strip().upper(), simulate_issues)
    if not isinstance(raw, dict):
        from app.core.errors import AppError

        raise AppError("AIRPORT_NOT_FOUND", "Unknown airport", http_status=404)
    from app.services.airports import normalize_airport_row

    return normalize_airport_row(raw, raw.get("city"))
