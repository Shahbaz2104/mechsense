"""Sensor reading queries.

PostgreSQL-specific design choices (documented in docs/architecture.md):
- `DISTINCT ON (machine_id)` for "latest reading per machine" — a single
  index-friendly pass over (machine_id, timestamp) instead of per-row queries.
"""

from datetime import datetime

from sqlalchemy import Select, func, select
from sqlalchemy.dialects.postgresql import distinct_on
from sqlalchemy.orm import Session

from app.models import ReadingSource, SensorReading


def _filtered(
    machine_id: int | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    source: str | None = None,
) -> Select:
    stmt = select(SensorReading)
    if machine_id is not None:
        stmt = stmt.where(SensorReading.machine_id == machine_id)
    if start is not None:
        stmt = stmt.where(SensorReading.timestamp >= start)
    if end is not None:
        stmt = stmt.where(SensorReading.timestamp <= end)
    if source:
        stmt = stmt.where(SensorReading.source == ReadingSource(source))
    return stmt


def list_readings(
    db: Session,
    *,
    machine_id: int | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    source: str | None = None,
    descending: bool = False,
    offset: int = 0,
    limit: int = 100,
) -> tuple[list[SensorReading], int]:
    stmt = _filtered(machine_id, start, end, source)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    ordering = SensorReading.timestamp.desc() if descending else SensorReading.timestamp.asc()
    rows = db.scalars(stmt.order_by(ordering, SensorReading.id).offset(offset).limit(limit)).all()
    return list(rows), int(total)


def latest_per_machine(
    db: Session, machine_ids: list[int] | None = None
) -> dict[int, SensorReading]:
    """Return {machine_id: latest reading} using PostgreSQL DISTINCT ON."""
    stmt = select(SensorReading)
    if machine_ids is not None:
        if not machine_ids:
            return {}
        stmt = stmt.where(SensorReading.machine_id.in_(machine_ids))
    stmt = stmt.ext(distinct_on(SensorReading.machine_id)).order_by(
        SensorReading.machine_id, SensorReading.timestamp.desc()
    )
    return {row.machine_id: row for row in db.scalars(stmt).all()}


def previous_reading(
    db: Session,
    *,
    machine_id: int,
    timestamp: datetime,
    exclude_reading_id: int,
) -> SensorReading | None:
    """The reading immediately before the given one for the same machine."""
    return db.scalar(
        select(SensorReading)
        .where(
            SensorReading.machine_id == machine_id,
            SensorReading.timestamp < timestamp,
            SensorReading.id != exclude_reading_id,
        )
        .order_by(SensorReading.timestamp.desc(), SensorReading.id.desc())
        .limit(1)
    )
