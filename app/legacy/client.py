from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx

from app.config import Settings
from app.core.errors import AppError, normalize_upstream_error_payload
from app.legacy.circuit import CircuitBreaker, CircuitOpen


class LegacyClient:
    def __init__(self, settings: Settings, breaker: CircuitBreaker | None = None) -> None:
        self._settings = settings
        self._breaker = breaker or CircuitBreaker(
            settings.circuit_failure_threshold,
            settings.circuit_open_seconds,
        )
        self._client = httpx.AsyncClient(
            base_url=settings.legacy_base_url.rstrip("/") + "/",
            timeout=httpx.Timeout(settings.http_timeout_seconds),
            headers={"Accept": "application/json", "User-Agent": "flight-bff-wrapper/1.0"},
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    def _with_simulate(self, params: dict[str, Any] | None, simulate_issues: bool) -> dict[str, Any] | None:
        out = dict(params) if params else {}
        if simulate_issues:
            out["simulate_issues"] = "true"
        return out or None

    async def _sleep_backoff(self, attempt: int) -> None:
        base = self._settings.retry_min_wait_seconds
        cap = self._settings.retry_max_wait_seconds
        delay = min(cap, base * (2**attempt))
        await asyncio.sleep(delay)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: Any = None,
        params: dict[str, Any] | None = None,
        simulate_issues: bool = False,
    ) -> Any:
        self._breaker.before_call()
        path = path.lstrip("/")
        last_error: Exception | None = None

        for attempt in range(self._settings.max_retries):
            try:
                resp = await self._client.request(
                    method,
                    path,
                    json=json_body,
                    params=self._with_simulate(params, simulate_issues),
                )
            except CircuitOpen as e:
                raise AppError("CIRCUIT_OPEN", str(e), http_status=503) from e
            except httpx.TimeoutException as e:
                last_error = e
                self._breaker.on_failure()
                if attempt + 1 >= self._settings.max_retries:
                    raise AppError("UPSTREAM_TIMEOUT", "Legacy API did not respond in time", http_status=504) from e
                await self._sleep_backoff(attempt)
                continue
            except httpx.NetworkError as e:
                last_error = e
                self._breaker.on_failure()
                if attempt + 1 >= self._settings.max_retries:
                    raise AppError("UPSTREAM_UNAVAILABLE", "Could not reach legacy API", http_status=502) from e
                await self._sleep_backoff(attempt)
                continue

            if resp.status_code == 429:
                self._breaker.on_failure()
                if attempt + 1 >= self._settings.max_retries:
                    raise AppError("UPSTREAM_RATE_LIMIT", "Legacy API rate limited the request", http_status=429)
                await self._sleep_backoff(attempt)
                continue

            if resp.status_code >= 500:
                self._breaker.on_failure()
                if attempt + 1 >= self._settings.max_retries:
                    raise AppError(
                        "UPSTREAM_ERROR",
                        f"Legacy API returned {resp.status_code}",
                        http_status=502,
                        details={"status_code": resp.status_code},
                    )
                await self._sleep_backoff(attempt)
                continue

            self._breaker.on_success()

            if resp.status_code >= 400:
                try:
                    payload = resp.json()
                except json.JSONDecodeError:
                    payload = {"message": resp.text[:500]}
                code, msg = normalize_upstream_error_payload(payload)
                raise AppError(
                    "LEGACY_ERROR",
                    msg,
                    http_status=resp.status_code if resp.status_code < 500 else 502,
                    details={"legacy_code": code, "status_code": resp.status_code},
                )

            if not resp.content:
                return None
            try:
                return resp.json()
            except json.JSONDecodeError as e:
                raise AppError("UPSTREAM_PARSE_ERROR", "Legacy API returned non-JSON", http_status=502) from e

        raise AppError("UPSTREAM_ERROR", "Legacy request failed after retries", http_status=502) from last_error

    async def flight_search(self, body: dict[str, Any], simulate_issues: bool) -> Any:
        return await self._request("POST", "api/v1/flightsearch", json_body=body, simulate_issues=simulate_issues)

    async def offer_details(self, offer_id: str, simulate_issues: bool) -> Any:
        return await self._request("GET", f"api/v2/offer/{offer_id}", simulate_issues=simulate_issues)

    async def create_booking(self, body: dict[str, Any], simulate_issues: bool) -> Any:
        return await self._request("POST", "booking/create", json_body=body, simulate_issues=simulate_issues)

    async def reservation(self, ref: str, simulate_issues: bool) -> Any:
        return await self._request("GET", f"api/v1/reservations/{ref}", simulate_issues=simulate_issues)

    async def airports_list(self, simulate_issues: bool) -> Any:
        return await self._request("GET", "api/airports", simulate_issues=simulate_issues)

    async def airport_one(self, code: str, simulate_issues: bool) -> Any:
        return await self._request("GET", f"api/airports/{code}", simulate_issues=simulate_issues)
