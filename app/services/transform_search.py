from __future__ import annotations

from typing import Any

from app.core.dates import parse_to_iso
from app.core.labels import AIRLINES, CABINS, aircraft_label
from app.schemas.api import LegSummary, OfferSummary


def _first_str(*vals: Any) -> str | None:
    for v in vals:
        if v is None:
            continue
        if isinstance(v, str) and v.strip():
            return v.strip()
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return str(v)
    return None


def _collect_legs(offer: dict[str, Any]) -> list[dict[str, Any]]:
    legs: list[dict[str, Any]] = []
    segments = (offer.get("segments") or {}).get("segment_list") or []
    for seg in segments:
        if not isinstance(seg, dict):
            continue
        for leg in seg.get("leg_data") or []:
            if isinstance(leg, dict):
                legs.append(leg)
    return legs


def _leg_summary(leg: dict[str, Any], city_by_code: dict[str, str]) -> LegSummary:
    dep = leg.get("departure_info") or {}
    arr = leg.get("arrival_info") or {}
    dep_ap = (dep.get("airport") or {}).get("code")
    arr_ap = (arr.get("airport") or {}).get("code")
    carrier = leg.get("carrier") or {}
    code = _first_str(carrier.get("marketing"), carrier.get("operating"), carrier.get("mktg_carrier")) or ""
    equip = leg.get("equipment") or {}
    ac = _first_str(equip.get("aircraft_code"), equip.get("type"))
    cabin = _first_str(leg.get("cabin"), leg.get("cabin_class"))
    fn = _first_str(carrier.get("number"), carrier.get("flight_no"))
    return LegSummary(
        departure_airport=str(dep_ap or "").upper(),
        departure_city=city_by_code.get(str(dep_ap or "").upper()),
        departure_terminal=_first_str((dep.get("airport") or {}).get("terminal")),
        departure_at=parse_to_iso(dep.get("scheduled_time") or dep.get("dt")),
        arrival_airport=str(arr_ap or "").upper(),
        arrival_city=city_by_code.get(str(arr_ap or "").upper()),
        arrival_terminal=_first_str((arr.get("airport") or {}).get("terminal")),
        arrival_at=parse_to_iso(arr.get("scheduled_time") or arr.get("arr_date")),
        marketing_carrier=code,
        marketing_carrier_name=AIRLINES.get(code),
        flight_number=fn,
        cabin_code=cabin,
        cabin_label=CABINS.get(cabin) if cabin else None,
        duration_minutes=leg.get("duration_minutes"),
        aircraft_code=ac,
        aircraft_label=aircraft_label(ac),
    )


def _price_block(pricing: dict[str, Any] | None) -> dict[str, Any]:
    p = pricing or {}
    total = p.get("totalAmountDecimal")
    if total is None:
        total = p.get("total")
    if total is None and p.get("total_amount") is not None:
        try:
            total = float(p["total_amount"])
        except (TypeError, ValueError):
            total = None
    currency = _first_str(p.get("currency"), p.get("CurrencyCode")) or "MYR"
    taxes_raw = ((p.get("taxes_fees") or {}).get("tax_breakdown")) or []
    taxes: list[dict[str, Any]] = []
    from app.core.labels import TAX_CODES

    for t in taxes_raw:
        if not isinstance(t, dict):
            continue
        c = str(t.get("code") or "")
        taxes.append({"code": c, "label": TAX_CODES.get(c), "amount": float(t.get("amount") or 0)})

    return {
        "total": float(total or 0),
        "currency": currency,
        "per_pax": p.get("per_pax"),
        "base_fare": p.get("base_fare") or p.get("BaseFare"),
        "taxes": taxes,
        "pax_count": p.get("pax_count"),
    }


def transform_offer(
    offer: dict[str, Any],
    *,
    direction: str,
    city_by_code: dict[str, str],
    search_id: str | None,
) -> OfferSummary | None:
    oid = _first_str(offer.get("offer_id"), offer.get("offerId"))
    if not oid:
        return None
    legs_raw = _collect_legs(offer)
    if not legs_raw:
        return None
    legs = [_leg_summary(l, city_by_code) for l in legs_raw]
    first, last = legs[0], legs[-1]
    airline_code = first.marketing_carrier
    stops = int(offer.get("num_stops") if offer.get("num_stops") is not None else offer.get("stops") or 0)
    duration_minutes = offer.get("total_journey_time")
    duration_display = _first_str(offer.get("total_journey"), offer.get("elapsed_time"))

    return OfferSummary(
        offer_id=oid,
        direction=direction,
        airline_code=airline_code,
        airline_name=AIRLINES.get(airline_code),
        departure={
            "airport": first.departure_airport,
            "city": first.departure_city,
            "terminal": first.departure_terminal,
            "at": first.departure_at,
        },
        arrival={
            "airport": last.arrival_airport,
            "city": last.arrival_city,
            "terminal": last.arrival_terminal,
            "at": last.arrival_at,
        },
        stops=stops,
        duration_minutes=int(duration_minutes) if duration_minutes is not None else None,
        duration_display=duration_display,
        price=_price_block(offer.get("pricing") if isinstance(offer.get("pricing"), dict) else {}),
        cabin_code=first.cabin_code,
        cabin_label=first.cabin_label,
        legs=legs,
        seats_remaining=offer.get("seats_remaining") or offer.get("avl_seats") or offer.get("seatAvailability"),
        refundable=offer.get("refundable") if offer.get("refundable") is not None else offer.get("isRefundable"),
        search_id=search_id,
    )


def transform_search_response(raw: dict[str, Any], city_by_code: dict[str, str]) -> list[OfferSummary]:
    data = raw.get("data") if isinstance(raw, dict) else None
    if not isinstance(data, dict):
        return []
    sid = _first_str(data.get("search_id"), data.get("SearchId"))
    fr = data.get("flight_results") or {}
    if not isinstance(fr, dict):
        return []
    out: list[OfferSummary] = []
    for direction in ("outbound", "inbound"):
        block = fr.get(direction) or {}
        if not isinstance(block, dict):
            continue
        for item in block.get("results") or []:
            if not isinstance(item, dict):
                continue
            o = transform_offer(item, direction=direction, city_by_code=city_by_code, search_id=sid)
            if o:
                out.append(o)
    return out
