"""Anomaly event listing, detail, and lifecycle actions."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.v1.pagination import PageDep, build_page, offset_for
from app.core.errors import NotFoundError
from app.db.session import get_db
from app.models import AnomalyEvent
from app.repositories import anomalies as anomaly_repo
from app.schemas.anomaly import (
    AnomalyActionRequest,
    AnomalyMethod,
    AnomalyRead,
    AnomalySeverity,
    AnomalyStatus,
)
from app.schemas.common import Page
from app.services import anomalies as anomaly_service

router = APIRouter(prefix="/anomalies", tags=["anomalies"])

DbDep = Annotated[Session, Depends(get_db)]
EventId = Annotated[int, Path(ge=1)]


def _load_event(db: Session, event_id: int) -> AnomalyEvent:
    event = db.scalar(
        select(AnomalyEvent)
        .where(AnomalyEvent.id == event_id)
        .options(selectinload(AnomalyEvent.reading))
        .execution_options(populate_existing=True)
    )
    if event is None:
        raise NotFoundError("Anomaly event", event_id)
    return event


@router.get("", response_model=Page[AnomalyRead], summary="List anomaly events")
def list_anomalies(
    db: DbDep,
    pagination: PageDep,
    machine_id: int | None = Query(default=None),
    status: AnomalyStatus | None = None,
    severity: AnomalySeverity | None = None,
    method: AnomalyMethod | None = None,
    metric: str | None = Query(default=None, max_length=32),
    start: datetime | None = None,
    end: datetime | None = None,
    q: str | None = Query(
        default=None,
        max_length=100,
        description="Substring match on explanation text or machine identifier/name",
    ),
    sort: str = Query(
        default="detected_at",
        pattern="^(detected_at|severity|metric|observed_value|status)$",
    ),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
) -> Page[AnomalyRead]:
    page, page_size = pagination
    items, total = anomaly_repo.list_events(
        db,
        machine_id=machine_id,
        status=status.value if status else None,
        severity=severity.value if severity else None,
        method=method.value if method else None,
        metric=metric,
        start=start,
        end=end,
        q=q,
        sort=sort,
        descending=order == "desc",
        offset=offset_for(page, page_size),
        limit=page_size,
    )
    return build_page(
        [AnomalyRead.model_validate(event) for event in items],
        total,
        page,
        page_size,
        Page[AnomalyRead],
    )


@router.get("/{anomaly_id}", response_model=AnomalyRead, summary="Anomaly detail")
def get_anomaly(anomaly_id: EventId, db: DbDep) -> AnomalyRead:
    return AnomalyRead.model_validate(_load_event(db, anomaly_id))


@router.post(
    "/{anomaly_id}/acknowledge",
    response_model=AnomalyRead,
    summary="Acknowledge an anomaly",
)
def acknowledge_anomaly(
    anomaly_id: EventId,
    db: DbDep,
    payload: AnomalyActionRequest | None = None,
) -> AnomalyRead:
    event = anomaly_service.acknowledge(db, anomaly_id, notes=payload.notes if payload else None)
    return AnomalyRead.model_validate(_load_event(db, event.id))


@router.post(
    "/{anomaly_id}/resolve",
    response_model=AnomalyRead,
    summary="Resolve an anomaly",
)
def resolve_anomaly(
    anomaly_id: EventId,
    db: DbDep,
    payload: AnomalyActionRequest | None = None,
) -> AnomalyRead:
    event = anomaly_service.resolve(db, anomaly_id, notes=payload.notes if payload else None)
    return AnomalyRead.model_validate(_load_event(db, event.id))
