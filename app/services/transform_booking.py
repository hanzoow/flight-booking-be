from __future__ import annotations

from typing import Any

from app.core.dates import parse_to_iso
from app.core.labels import BOOKING_STATUS, PASSENGER_TYPES
from app.schemas.api import BookingConfirmation, BookingPassengerOut


def _pick_reservation(payload: dict[str, Any]) -> dict[str, Any] | None:
    data = payload.get("data")
    if not isinstance(data, dict):
        return None
    r = data.get("reservation") or data.get("Reservation")
    return r if isinstance(r, dict) else None


def transform_booking(raw: dict[str, Any]) -> BookingConfirmation | None:
    data = raw.get("data")
    if isinstance(data, dict) and "booking_ref" in data:
        res = data
    else:
        res = _pick_reservation(raw) or (data if isinstance(data, dict) else None)
    if not isinstance(res, dict):
        return None

    pax_out: list[BookingPassengerOut] = []
    for p in res.get("passengers") or []:
        if not isinstance(p, dict):
            continue
        ptype = p.get("type") or p.get("PaxType")
        dob_raw = p.get("dob") or p.get("DateOfBirth")
        pax_out.append(
            BookingPassengerOut(
                id=str(p.get("pax_id")) if p.get("pax_id") else None,
                title=p.get("title"),
                first_name=str(p.get("first_name") or p.get("FirstName") or ""),
                last_name=str(p.get("last_name") or p.get("LastName") or ""),
                date_of_birth=str(dob_raw) if dob_raw else None,
                nationality=p.get("nationality"),
                passport_number=p.get("passport_no"),
                type_code=str(ptype) if ptype else None,
                type_label=PASSENGER_TYPES.get(str(ptype), str(ptype) if ptype else None),
            )
        )

    contact = res.get("contact") or {}
    contact_out = {
        "email": contact.get("email") or contact.get("EmailAddress"),
        "phone": contact.get("phone"),
    }

    tick = res.get("ticketing") or {}
    ticketing_out = {
        "status": tick.get("status"),
        "time_limit_at": parse_to_iso(tick.get("time_limit")),
        "ticket_numbers": tick.get("ticket_numbers") or [],
    }

    st_code = res.get("StatusCode")
    status_label = BOOKING_STATUS.get(str(st_code), None) if st_code else None

    created = parse_to_iso(res.get("created_at")) or parse_to_iso(res.get("CreatedDateTime"))

    return BookingConfirmation(
        booking_reference=str(res.get("booking_ref") or res.get("BookingReference") or ""),
        pnr=str(res.get("pnr") or res.get("PNR") or "") or None,
        status=str(res.get("status") or "UNKNOWN"),
        status_code=str(st_code) if st_code else None,
        status_label=status_label,
        offer_id=str(res.get("offer_id") or ""),
        passengers=pax_out,
        contact=contact_out,
        ticketing=ticketing_out,
        created_at=created,
    )
