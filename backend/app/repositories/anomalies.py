"""Anomaly event queries."""

from datetime import datetime

from sqlalchemy import ColumnElement, case, func, or_, select
from sqlalchemy.dialects.postgresql import distinct_on
from sqlalchemy.orm import Session, selectinload

from app.models import AnomalyEvent, AnomalyMethod, AnomalySeverity, AnomalyStatus, Machine
from app.schemas.anomaly import AnomalyCounts


def active_event(
    db: Session, *, machine_id: int, metric: str, method: AnomalyMethod
) -> AnomalyEvent | None:
    """The current open/acknowledged event for (machine, metric, method), if any."""
    return db.scalar(
        select(AnomalyEvent)
        .where(
            AnomalyEvent.machine_id == machine_id,
            AnomalyEvent.metric == metric,
            AnomalyEvent.method == method,
            AnomalyEvent.status.in_([AnomalyStatus.open, AnomalyStatus.acknowledged]),
        )
        .order_by(AnomalyEvent.detected_at.desc())
        .limit(1)
    )


def get_event(db: Session, event_id: int) -> AnomalyEvent | None:
    return db.get(AnomalyEvent, event_id)


def list_events(
    db: Session,
    *,
    machine_id: int | None = None,
    status: str | None = None,
    severity: str | None = None,
    method: str | None = None,
    metric: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    q: str | None = None,
    sort: str = "detected_at",
    descending: bool = True,
    offset: int = 0,
    limit: int = 25,
) -> tuple[list[AnomalyEvent], int]:
    stmt = select(AnomalyEvent)
    if machine_id is not None:
        stmt = stmt.where(AnomalyEvent.machine_id == machine_id)
    if status:
        stmt = stmt.where(AnomalyEvent.status == AnomalyStatus(status))
    if severity:
        stmt = stmt.where(AnomalyEvent.severity == severity)
    if method:
        stmt = stmt.where(AnomalyEvent.method == AnomalyMethod(method))
    if metric:
        stmt = stmt.where(AnomalyEvent.metric == metric)
    if start is not None:
        stmt = stmt.where(AnomalyEvent.detected_at >= start)
    if end is not None:
        stmt = stmt.where(AnomalyEvent.detected_at <= end)
    if q:
        pattern = f"%{q}%"
        stmt = stmt.join(AnomalyEvent.machine).where(
            or_(
                AnomalyEvent.explanation.ilike(pattern),
                Machine.identifier.ilike(pattern),
                Machine.name.ilike(pattern),
            )
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    sort_columns: dict[str, ColumnElement] = {
        "detected_at": AnomalyEvent.detected_at,
        "metric": AnomalyEvent.metric,
        "observed_value": AnomalyEvent.observed_value,
        "status": AnomalyEvent.status,
        # warning=0, critical=1 so descending puts critical first.
        "severity": case((AnomalyEvent.severity == AnomalySeverity.critical, 1), else_=0),
    }
    primary = sort_columns[sort]
    primary_order = primary.desc() if descending else primary.asc()
    stmt = (
        stmt.options(selectinload(AnomalyEvent.reading))
        .order_by(primary_order, AnomalyEvent.id)
        .offset(offset)
        .limit(limit)
    )
    rows = db.scalars(stmt).all()
    return list(rows), int(total)


def open_alert_count(db: Session) -> int:
    """Open, not-yet-acknowledged events = active alerts."""
    return int(
        db.scalar(
            select(func.count())
            .select_from(AnomalyEvent)
            .where(AnomalyEvent.status == AnomalyStatus.open)
        )
        or 0
    )


def count_period(db: Session, *, start: datetime, end: datetime, status: str | None = None) -> int:
    stmt = (
        select(func.count())
        .select_from(AnomalyEvent)
        .where(
            AnomalyEvent.detected_at >= start,
            AnomalyEvent.detected_at < end,
        )
    )
    if status:
        stmt = stmt.where(AnomalyEvent.status == AnomalyStatus(status))
    return int(db.scalar(stmt) or 0)


def counts_by_status_severity(
    db: Session, *, machine_id: int | None = None, start: datetime | None = None
) -> AnomalyCounts:
    stmt = select(
        AnomalyEvent.status,
        AnomalyEvent.severity,
        func.count(),
    ).group_by(AnomalyEvent.status, AnomalyEvent.severity)
    if machine_id is not None:
        stmt = stmt.where(AnomalyEvent.machine_id == machine_id)
    if start is not None:
        stmt = stmt.where(AnomalyEvent.detected_at >= start)

    counts = AnomalyCounts()
    for status, severity, count in db.execute(stmt):
        if status == AnomalyStatus.open:
            counts.open += count
        elif status == AnomalyStatus.acknowledged:
            counts.acknowledged += count
        elif status == AnomalyStatus.resolved:
            counts.resolved += count
        if severity == "warning" or getattr(severity, "value", severity) == "warning":
            counts.warning += count
        else:
            counts.critical += count
    return counts


def latest_per_machine(db: Session) -> dict[int, AnomalyEvent]:
    """Most recent event (any status) per machine — dashboard 'recent anomaly'."""
    stmt = (
        select(AnomalyEvent)
        .ext(distinct_on(AnomalyEvent.machine_id))
        .order_by(AnomalyEvent.machine_id, AnomalyEvent.detected_at.desc())
    )
    return {row.machine_id: row for row in db.scalars(stmt).all()}
