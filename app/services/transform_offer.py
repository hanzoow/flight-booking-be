from __future__ import annotations

from typing import Any

from app.core.dates import parse_to_iso
from app.core.labels import payment_method_label
from app.schemas.api import Money


def transform_offer_details(raw: dict[str, Any]) -> dict[str, Any]:
    data = raw.get("data") if isinstance(raw, dict) else None
    offer = (data or {}).get("offer") if isinstance(data, dict) else None
    if not isinstance(offer, dict):
        return {}

    fd = offer.get("fare_details") or {}
    rules = (fd.get("rules") or {}) if isinstance(fd, dict) else {}
    baggage = offer.get("baggage_allowance") or {}
    conditions = offer.get("conditions") or {}
    pay = offer.get("payment_requirements") or {}

    def money_block(obj: Any) -> dict[str, Any] | None:
        if not isinstance(obj, dict):
            return None
        amt = obj.get("amount")
        cur = obj.get("currency") or obj.get("CurrencyCode")
        if amt is None or cur is None:
            return None
        return Money(amount=float(amt), currency=str(cur)).model_dump()

    refund = rules.get("refund") if isinstance(rules.get("refund"), dict) else {}
    change = rules.get("change") if isinstance(rules.get("change"), dict) else {}
    no_show = rules.get("no_show") if isinstance(rules.get("no_show"), dict) else {}

    methods = pay.get("accepted_methods") if isinstance(pay.get("accepted_methods"), list) else []
    labeled = [{"code": str(m), "label": payment_method_label(str(m))} for m in methods]

    meta = raw.get("meta") if isinstance(raw.get("meta"), dict) else {}

    return {
        "offer_id": offer.get("id") or offer.get("offer_id"),
        "status": offer.get("status"),
        "status_code": offer.get("StatusCode"),
        "fare_family": fd.get("fare_family") or fd.get("FareFamily"),
        "rules": {
            "refund": {
                "allowed": refund.get("allowed"),
                "penalty": money_block(refund.get("penalty")),
            },
            "change": {
                "allowed": change.get("allowed"),
                "penalty": money_block(change.get("penalty")),
            },
            "no_show": {
                "penalty": money_block((no_show.get("penalty") or {}) if isinstance(no_show, dict) else {}),
            },
        },
        "baggage": {
            "checked": baggage.get("checked"),
            "carry_on": baggage.get("carry_on"),
        },
        "conditions": conditions,
        "payment": {
            "accepted_methods": labeled,
            "time_limit_at": parse_to_iso(pay.get("time_limit")),
            "instant_ticketing_required": pay.get("instant_ticketing_required"),
        },
        "timestamps": {
            "created_at": parse_to_iso(offer.get("created_at")),
            "expires_at": parse_to_iso(offer.get("expires_at")),
        },
        "meta": {"request_id": meta.get("request_id"), "provider": meta.get("provider")},
    }
