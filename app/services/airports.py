from __future__ import annotations

import asyncio
import logging
from typing import Any

from cachetools import TTLCache

from app.config import Settings
from app.legacy.client import LegacyClient
from app.schemas.api import AirportOut

logger = logging.getLogger(__name__)


class AirportIndex:
    def __init__(self, settings: Settings) -> None:
        self._ttl = TTLCache(maxsize=2, ttl=settings.airport_cache_ttl_seconds)
        self._settings = settings

    def _cache_key(self, simulate_issues: bool) -> str:
        return f"sim:{simulate_issues}"

    async def get_all(self, client: LegacyClient, simulate_issues: bool) -> list[AirportOut]:
        key = self._cache_key(simulate_issues)
        if key in self._ttl:
            return self._ttl[key]

        raw = await client.airports_list(simulate_issues)
        rows = raw.get("airports") if isinstance(raw, dict) else None
        if not isinstance(rows, list):
            rows = []

        async def enrich(row: dict[str, Any]) -> AirportOut:
            code = str(row.get("code") or row.get("IATA") or "").upper()
            city: str | None = None
            try:
                one = await client.airport_one(code, simulate_issues)
                if isinstance(one, dict):
                    city = one.get("city")
            except Exception:
                logger.debug("Airport detail fetch failed for %s", code, exc_info=True)
            return normalize_airport_row(row, city)

        enriched = await asyncio.gather(*[enrich(r) for r in rows if isinstance(r, dict)])
        out = list(enriched)
        self._ttl[key] = out
        return out

    async def city_map(self, client: LegacyClient, simulate_issues: bool) -> dict[str, str]:
        airports = await self.get_all(client, simulate_issues)
        return {a.code: c for a in airports if (c := a.city)}


def normalize_airport_row(row: dict[str, Any], city: str | None = None) -> AirportOut:
    code = str(row.get("code") or row.get("IATA") or "").upper()
    cc = row.get("country_code") or row.get("CC")
    tz = row.get("tz_offset")
    coords = row.get("coordinates") or {}
    lat = coords.get("lat") or coords.get("latitude")
    lng = coords.get("lng") or coords.get("longitude")
    return AirportOut(
        code=code,
        city=city or row.get("city"),
        country_code=str(cc).upper() if cc else None,
        tz_offset_hours=int(tz) if tz is not None else None,
        latitude=float(lat) if lat is not None else None,
        longitude=float(lng) if lng is not None else None,
    )
