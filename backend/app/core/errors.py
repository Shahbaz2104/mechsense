"""Application errors and consistent HTTP error envelopes."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("mechsense.errors")


class AppError(Exception):
    """Base application error carrying an HTTP status and stable machine code."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: list[dict] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


class NotFoundError(AppError):
    def __init__(self, resource: str, identifier: object) -> None:
        super().__init__(
            status_code=404,
            code="not_found",
            message=f"{resource} '{identifier}' not found",
        )


class ConflictError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(status_code=409, code="conflict", message=message)


class ValidationProblem(AppError):
    def __init__(self, message: str, details: list[dict] | None = None) -> None:
        super().__init__(status_code=422, code="validation_error", message=message, details=details)


def _envelope(code: str, message: str, details: list[dict] | None = None) -> dict:
    body: dict = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return body


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = {
            400: "bad_request",
            401: "unauthorized",
            403: "forbidden",
            404: "not_found",
            405: "method_not_allowed",
            409: "conflict",
            429: "rate_limited",
        }.get(exc.status_code, "http_error")
        detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(code, detail),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {
                "field": ".".join(str(part) for part in err.get("loc", ())),
                "message": err.get("msg", "invalid value"),
                "type": err.get("type", ""),
            }
            for err in exc.errors()
        ]
        logger.info("validation_failed", extra={"detail_count": len(details)})
        return JSONResponse(
            status_code=422,
            content=_envelope("validation_error", "Request validation failed", details),
        )
