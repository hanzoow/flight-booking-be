from __future__ import annotations

from app.core import labels as L
from app.schemas.api import ReferenceLabelsResponse


def build_reference_labels() -> ReferenceLabelsResponse:
    return ReferenceLabelsResponse(
        airlines=dict(L.AIRLINES),
        cabins=dict(L.CABINS),
        aircraft=dict(L.AIRCRAFT_TYPES),
        tax_codes=dict(L.TAX_CODES),
        passenger_types=dict(L.PASSENGER_TYPES),
    )
