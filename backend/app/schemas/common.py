"""Shared API schemas: pagination envelope and error responses."""

from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page[T](BaseModel):
    """Standard paginated response envelope."""

    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[dict] | None = None


class ErrorResponse(BaseModel):
    """Consistent error envelope for all non-2xx responses."""

    error: ErrorBody
