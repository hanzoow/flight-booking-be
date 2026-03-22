---
name: flight-bff-extend-api
description: >-
  Adds a new BFF endpoint that wraps the legacy mock-travel API with consistent
  REST shape, unified errors, optional TTL caching, and OpenAPI docs. Use when
  the user asks for a new API route, new legacy integration, caching on a
  endpoint, or to extend this FastAPI flight wrapper following project patterns.
---

# Extend the Flight BFF (new legacy-backed endpoint)

Follow this checklist so new code matches `.cursor/rules/` and existing modules.

## 1. Discover upstream

- Read legacy OpenAPI: `{LEGACY_BASE_URL}/openapi.json` or `/docs`.
- Note method, path, request schema, and **error shapes** (this API has multiple legacy formats — all must map through `normalize_upstream_error_payload` in `app/core/errors.py` if a new variant appears; extend that function only when needed).

## 2. Legacy client

- Add an async method on `LegacyClient` in `app/legacy/client.py` that calls `_request(...)` with the correct path and `simulate_issues` forwarded.
- Do **not** add response transformation here.

## 3. Public contract

- Add Pydantic models in `app/schemas/api.py` for **wrapper** request/response (flat, UI-oriented names).
- Reuse `parse_to_iso` / label maps in `app/core/` when exposing dates or codes.

## 4. Transform layer

- Add or extend a module under `app/services/` (e.g. `transform_foo.py`) that accepts raw `dict` and returns Pydantic models or plain dicts ready for `response_model`.
- Keep **upstream field names** out of public models unless intentional.

## 5. Route

- Add a router under `app/api/routes/` (or extend an existing router) with:
  - `APIRouter(prefix=..., tags=[...])`
  - `simulate_issues: bool = Query(False, description=...)`
  - `LegacyDep` (and other deps) via `Annotated` + `Depends`
  - `response_model` where helpful
- Register the router in `app/main.py` under `/v1` like existing routes.

## 6. Caching (optional)

- Decide using the rule **flight-bff-caching-resilience**: only if data is reference-like or explicitly safe to stale.
- Implement with `TTLCache` + `Settings` TTL field + README env table row.
- For GET, optionally set a response header (e.g. `X-Cache`) for demos.

## 7. Verify

- Run `uvicorn app.main:app --reload` and exercise `/docs`.
- One happy-path `curl` and one legacy error path (expect unified `error` JSON).
- If new env vars: update `app/config.py`, `render.yaml` if needed, and README.

## Reference layout

```text
app/api/routes/<feature>.py   # HTTP
app/schemas/api.py            # outward models
app/services/transform_*.py   # legacy → outward
app/legacy/client.py          # HTTP + retry + breaker
app/core/errors.py            # AppError + legacy error normalization
```
