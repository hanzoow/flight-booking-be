from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query, Request, Response

from app.api.deps import LegacyDep
from app.schemas.api import BookingConfirmation, CreateBookingBody
from app.services.transform_booking import transform_booking

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingConfirmation)
async def create_booking(
    body: CreateBookingBody,
    legacy: LegacyDep,
    request: Request,
    simulate_issues: bool = Query(False),
) -> BookingConfirmation:
    passengers: list[dict[str, Any]] = []
    for p in body.passengers:
        d = {
            "first_name": p.first_name,
            "last_name": p.last_name,
            "title": p.title,
            "dob": p.dob,
            "nationality": p.nationality.upper() if p.nationality else None,
            "passport_no": p.passport_no,
            "email": str(p.email) if p.email else None,
            "phone": p.phone,
        }
        passengers.append({k: v for k, v in d.items() if v is not None})

    legacy_body = {
        "offer_id": body.offer_id,
        "contact_email": str(body.contact_email),
        "contact_phone": body.contact_phone,
        "passengers": passengers,
    }
    raw = await legacy.create_booking(legacy_body, simulate_issues)
    conf = transform_booking(raw if isinstance(raw, dict) else {})
    if conf is None:
        from app.core.errors import AppError

        raise AppError("BOOKING_PARSE_ERROR", "Unexpected booking response from legacy API", http_status=502)
    cache = request.app.state.booking_cache
    cache[conf.booking_reference] = conf.model_dump()
    return conf


@router.get("/{reference}", response_model=BookingConfirmation)
async def get_booking(
    reference: str,
    legacy: LegacyDep,
    request: Request,
    response: Response,
    simulate_issues: bool = Query(False),
) -> BookingConfirmation:
    ref = reference.strip().upper()
    cache = request.app.state.booking_cache
    if ref in cache:
        response.headers["X-Cache"] = "HIT"
        return BookingConfirmation.model_validate(cache[ref])
    response.headers["X-Cache"] = "MISS"
    raw = await legacy.reservation(ref, simulate_issues)
    conf = transform_booking(raw if isinstance(raw, dict) else {})
    if conf is None:
        from app.core.errors import AppError

        raise AppError("BOOKING_NOT_FOUND", "Booking could not be loaded", http_status=404)
    cache[ref] = conf.model_dump()
    return conf
