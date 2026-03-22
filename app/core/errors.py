from __future__ import annotations

import uuid
from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        http_status: int = status.HTTP_502_BAD_GATEWAY,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.http_status = http_status
        self.details = details or {}


def error_body(code: str, message: str, details: dict[str, Any] | None = None, request_id: str | None = None) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "request_id": request_id or str(uuid.uuid4()),
        }
    }


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    rid = getattr(request.state, "request_id", None) or str(uuid.uuid4())
    body = error_body(exc.code, exc.message, exc.details, rid)
    return JSONResponse(status_code=exc.http_status, content=body)


def normalize_upstream_error_payload(payload: Any) -> tuple[str, str]:
    if not isinstance(payload, dict):
        return "UPSTREAM_ERROR", "Unexpected upstream response"

    err = payload.get("error")
    if isinstance(err, dict) and ("message" in err or "msg" in err):
        msg = str(err.get("message") or err.get("msg") or "Upstream error")
        code = str(err.get("code", "UPSTREAM_ERROR"))
        return code, msg

    errors = payload.get("errors")
    if isinstance(errors, list) and errors:
        first = errors[0]
        if isinstance(first, dict):
            msg = str(first.get("detail") or first.get("message") or "Upstream error")
            code = str(first.get("code", "UPSTREAM_ERROR"))
            return code, msg

    fault = payload.get("fault")
    if isinstance(fault, dict):
        msg = str(fault.get("faultstring") or "Upstream fault")
        code = str(fault.get("faultcode", "UPSTREAM_FAULT"))
        return code, msg

    if payload.get("status") == "error":
        return "UPSTREAM_ERROR", str(payload.get("msg") or "Upstream error")

    detail = payload.get("detail")
    if isinstance(detail, list):
        parts = []
        for item in detail:
            if isinstance(item, dict):
                parts.append(str(item.get("msg", item)))
        if parts:
            return "VALIDATION_ERROR", "; ".join(parts)

    return "UPSTREAM_ERROR", str(payload.get("message") or payload.get("msg") or "Upstream error")
