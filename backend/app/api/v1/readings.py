"""Sensor reading queries and ingestion."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.api.v1.pagination import PageDep, build_page, offset_for
from app.db.session import get_db
from app.repositories import readings as reading_repo
from app.schemas.common import Page
from app.schemas.reading import (
    ReadingCreate,
    ReadingIngestResponse,
    ReadingRead,
    ReadingSource,
)
from app.services import readings as reading_service
from app.services.machines import get_machine_or_404

router = APIRouter(tags=["readings"])

DbDep = Annotated[Session, Depends(get_db)]


def _readings_page(
    db: Session,
    pagination: tuple[int, int],
    *,
    machine_id: int | None,
    start: datetime | None,
    end: datetime | None,
    source: ReadingSource | None,
    order: str,
) -> Page[ReadingRead]:
    page, page_size = pagination
    items, total = reading_repo.list_readings(
        db,
        machine_id=machine_id,
        start=start,
        end=end,
        source=source.value if source else None,
        descending=order == "desc",
        offset=offset_for(page, page_size),
        limit=page_size,
    )
    return build_page(
        [ReadingRead.model_validate(reading) for reading in items],
        total,
        page,
        page_size,
        Page[ReadingRead],
    )


@router.post(
    "/readings",
    response_model=ReadingIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a sensor reading",
)
def ingest_reading(payload: ReadingCreate, db: DbDep) -> ReadingIngestResponse:
    """Accept one reading, run threshold detection, report affected events."""
    reading, events = reading_service.ingest_reading(db, payload)
    return ReadingIngestResponse(
        reading=ReadingRead.model_validate(reading),
        affected_anomaly_ids=[event.id for event in events],
    )


@router.get("/readings", response_model=Page[ReadingRead], summary="List readings")
def list_readings(
    db: DbDep,
    pagination: PageDep,
    machine_id: int | None = Query(default=None),
    start: datetime | None = Query(
        default=None, description="Inclusive lower timestamp bound (ISO 8601, tz-aware)"
    ),
    end: datetime | None = Query(
        default=None, description="Inclusive upper timestamp bound (ISO 8601, tz-aware)"
    ),
    source: ReadingSource | None = None,
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
) -> Page[ReadingRead]:
    return _readings_page(
        db, pagination, machine_id=machine_id, start=start, end=end, source=source, order=order
    )


@router.get(
    "/machines/{machine_id}/readings",
    response_model=Page[ReadingRead],
    summary="Machine readings",
)
def list_machine_readings(
    machine_id: Annotated[int, Path(ge=1)],
    db: DbDep,
    pagination: PageDep,
    start: datetime | None = None,
    end: datetime | None = None,
    source: ReadingSource | None = None,
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
) -> Page[ReadingRead]:
    get_machine_or_404(db, machine_id)
    return _readings_page(
        db, pagination, machine_id=machine_id, start=start, end=end, source=source, order=order
    )
