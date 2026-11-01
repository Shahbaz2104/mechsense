"""Shared pagination dependency."""

from collections.abc import Callable
from math import ceil
from typing import Annotated

from fastapi import Depends, Query

from app.core.config import get_settings

_settings = get_settings()


def page_params(
    page: int = Query(1, ge=1, description="1-based page number"),
    page_size: int = Query(
        _settings.default_page_size,
        ge=1,
        le=_settings.max_page_size,
        description=f"Items per page (max {_settings.max_page_size})",
    ),
) -> tuple[int, int]:
    return page, page_size


PageDep = Annotated[tuple[int, int], Depends(page_params)]


def offset_for(page: int, page_size: int) -> int:
    return (page - 1) * page_size


def build_page(items: list, total: int, page: int, page_size: int, page_model):
    return page_model(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total else 0,
    )


PaginationCallable = Callable[..., tuple[int, int]]
