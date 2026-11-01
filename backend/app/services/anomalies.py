"""Anomaly event lifecycle: acknowledge and resolve actions.

Acknowledgment != resolution:
- acknowledge: an engineer has seen the alert (status open -> acknowledged).
- resolve: the investigation is finished (open/acknowledged -> resolved).
Both actions store their own timestamp and optional notes; the history
columns (acknowledged_at / resolved_at) are preserved independently.
"""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.errors import AppError, NotFoundError
from app.models import AnomalyEvent, AnomalyStatus
from app.repositories import anomalies as anomaly_repo


def get_event_or_404(db: Session, event_id: int) -> AnomalyEvent:
    event = anomaly_repo.get_event(db, event_id)
    if event is None:
        raise NotFoundError("Anomaly event", event_id)
    return event


def acknowledge(db: Session, event_id: int, notes: str | None = None) -> AnomalyEvent:
    event = get_event_or_404(db, event_id)
    if event.status == AnomalyStatus.resolved:
        raise AppError(
            status_code=409,
            code="invalid_state",
            message="A resolved anomaly event cannot be acknowledged again",
        )
    if event.status == AnomalyStatus.open:
        event.status = AnomalyStatus.acknowledged
        event.acknowledged_at = datetime.now(UTC)
    if notes is not None:
        event.notes = notes
    db.commit()
    db.refresh(event)
    return event


def resolve(db: Session, event_id: int, notes: str | None = None) -> AnomalyEvent:
    event = get_event_or_404(db, event_id)
    if event.status == AnomalyStatus.resolved:
        # Idempotent: resolving an already resolved event just updates notes.
        if notes is not None:
            event.notes = notes
            db.commit()
            db.refresh(event)
        return event
    # Resolving straight from `open` is allowed; acknowledged_at stays NULL
    # because no acknowledgment actually happened (the two are not conflated).
    event.status = AnomalyStatus.resolved
    event.resolved_at = datetime.now(UTC)
    if notes is not None:
        event.notes = notes
    db.commit()
    db.refresh(event)
    return event
