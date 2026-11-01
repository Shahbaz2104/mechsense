"""Sensor reading ingestion: persistence + detection handoff.

This is the single write path for readings (API ingest, simulation step and
CSV import all funnel here), so validation, duplicate handling and anomaly
detection stay consistent — and testable outside route handlers.
"""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.detection import service as detection_service
from app.models import AnomalyEvent, SensorReading
from app.repositories import machines as machine_repo
from app.schemas.reading import ReadingCreate


def ingest_reading(db: Session, payload: ReadingCreate) -> tuple[SensorReading, list[AnomalyEvent]]:
    """Store one reading and run threshold detection.

    Returns the persisted reading and the anomaly events the reading created
    or extended. Raises ConflictError when (machine_id, timestamp) already
    exists. Caller's session: commits on success, rolls back on conflict.
    """
    machine = machine_repo.get_machine(db, payload.machine_id)
    if machine is None:
        raise NotFoundError("Machine", payload.machine_id)

    timestamp = payload.timestamp or datetime.now(UTC)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)

    reading = SensorReading(
        machine_id=payload.machine_id,
        timestamp=timestamp,
        vibration_rms=Decimal(str(payload.vibration_rms)),
        temperature=Decimal(str(payload.temperature)),
        rpm=Decimal(str(payload.rpm)),
        load_pct=Decimal(str(payload.load_pct)),
        pressure=Decimal(str(payload.pressure)) if payload.pressure is not None else None,
        source=payload.source,
    )
    db.add(reading)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise ConflictError(
            f"A reading for machine {payload.machine_id} already exists at {timestamp.isoformat()}"
        ) from None

    events = detection_service.process_reading(db, reading)
    db.commit()
    db.refresh(reading)
    return reading, events
