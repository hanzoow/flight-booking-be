from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import LegacyDep
from app.core.errors import AppError
from app.services.transform_offer import transform_offer_details

router = APIRouter(prefix="/flights/offers", tags=["offers"])


@router.get("/{offer_id}")
async def get_offer(
    offer_id: str,
    legacy: LegacyDep,
    simulate_issues: bool = Query(False, description="Forward to legacy API to simulate instability"),
) -> dict:
    raw = await legacy.offer_details(offer_id.strip(), simulate_issues)
    out = transform_offer_details(raw if isinstance(raw, dict) else {})
    if not out.get("offer_id"):
        raise AppError("OFFER_NOT_FOUND", "Offer could not be loaded", http_status=404)
    return out
