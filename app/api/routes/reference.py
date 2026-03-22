from __future__ import annotations

from fastapi import APIRouter, Response

from app.schemas.api import ReferenceLabelsResponse
from app.services.reference_labels import build_reference_labels

router = APIRouter(prefix="/reference", tags=["reference"])

# Browsers and CDNs can cache; data is static and does not call legacy.
_CACHE_CONTROL = "public, max-age=86400, stale-while-revalidate=604800"


@router.get(
    "/labels",
    response_model=ReferenceLabelsResponse,
    summary="Reference label maps",
    description=(
        "Returns airline, cabin, aircraft, tax, and passenger-type code → label maps from BFF configuration. "
        "Does not call the legacy API. Safe to cache on the client."
    ),
)
async def get_reference_labels(response: Response) -> ReferenceLabelsResponse:
    response.headers["Cache-Control"] = _CACHE_CONTROL
    return build_reference_labels()
