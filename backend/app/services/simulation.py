"""Interactive demo simulation: one-step reading and batch demo generation.

Both actions append NEW readings after a machine's current history (never
backfill), run threshold detection, and commit atomically — the frontend can
safely poll step/live-toggle without duplicate-timestamp collisions.

Step uses the single-write path (services.readings.ingest_reading); the batch
path stages all readings first and commits once, mirroring the import service.
"""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError, ConflictError, NotFoundError, ValidationProblem
from app.detection import service as detection_service
from app.models import Machine, MachineStatus, ReadingSource, SensorReading
from app.schemas.reading import ReadingCreate, ReadingIngestResponse, ReadingRead
from app.schemas.simulation import DemoGenerateRequest, DemoGenerateResponse
from app.services import readings as readings_service
from app.simulation import generator


def _last_timestamp(db: Session, machine_id: int) -> datetime | None:
    return db.scalar(
        select(func.max(SensorReading.timestamp)).where(SensorReading.machine_id == machine_id)
    )


def _next_row(machine: Machine, after: datetime | None) -> dict:
    """Next reading strictly after `after`, anchored to the 5-minute grid.

    With history present the timestamp is exactly last + READ_INTERVAL (rapid
    clicks step the simulated clock forward, not the wall clock); from an empty
    machine it starts at the current time.
    """
    settings = get_settings()
    profile = generator.profile_for(machine.identifier)
    now = datetime.now(UTC)
    # Fresh/catch-up history jumps to the present; an already-current machine
    # continues its 5-minute grid (rapid clicks step simulated time, not wall).
    anchor = max(after + generator.READ_INTERVAL, now) if after is not None else now
    return generator.generate_next_reading(
        profile,
        machine_identifier=machine.identifier,
        base_seed=settings.simulation_seed,
        after=after,
        interval=generator.READ_INTERVAL,
        has_pressure="pressure" in (machine.thresholds or {}),
        now=anchor,
    )


def step(db: Session, machine_id: int) -> ReadingIngestResponse:
    """Generate, persist and detect the next plausible reading for a machine."""
    machine = db.get(Machine, machine_id)
    if machine is None:
        raise NotFoundError("Machine", machine_id)
    if machine.status != MachineStatus.active:
        raise AppError(
            status_code=409,
            code="invalid_state",
            message="Machine is inactive; activate it before simulating readings",
        )

    row = _next_row(machine, _last_timestamp(db, machine.id))
    reading, events = readings_service.ingest_reading(
        db,
        ReadingCreate(
            machine_id=machine.id,
            timestamp=row["timestamp"],
            vibration_rms=row["vibration_rms"],
            temperature=row["temperature"],
            rpm=row["rpm"],
            load_pct=row["load_pct"],
            pressure=row["pressure"],
            source=ReadingSource.simulated,
        ),
    )
    return ReadingIngestResponse(
        reading=ReadingRead.model_validate(reading),
        affected_anomaly_ids=[event.id for event in events],
    )


def generate_demo(db: Session, payload: DemoGenerateRequest) -> DemoGenerateResponse:
    """Append `count` readings per active machine (or one machine) in one batch."""
    settings = get_settings()
    if payload.count > settings.simulation_max_batch:
        raise ValidationProblem(
            f"count {payload.count} exceeds the batch limit of {settings.simulation_max_batch}"
        )

    if payload.machine_id is not None:
        machine = db.get(Machine, payload.machine_id)
        if machine is None:
            raise NotFoundError("Machine", payload.machine_id)
        if machine.status != MachineStatus.active:
            raise AppError(
                status_code=409,
                code="invalid_state",
                message="Machine is inactive; activate it before simulating readings",
            )
        targets = [machine]
        skipped: list[str] = []
    else:
        all_machines = list(db.scalars(select(Machine).order_by(Machine.id)))
        targets = [m for m in all_machines if m.status == MachineStatus.active]
        skipped = [m.identifier for m in all_machines if m.status != MachineStatus.active]

    planned = len(targets) * payload.count
    if planned > settings.simulation_max_batch:
        raise ValidationProblem(
            f"would create {planned} readings; the batch limit is "
            f"{settings.simulation_max_batch} — lower count or target a single machine"
        )
    if not targets:
        return DemoGenerateResponse(
            machines_processed=0,
            readings_created=0,
            anomaly_events_created=0,
            skipped_inactive=skipped,
        )

    readings: list[SensorReading] = []
    try:
        for machine in targets:
            after = _last_timestamp(db, machine.id)
            for _ in range(payload.count):
                row = _next_row(machine, after)
                after = row["timestamp"]
                readings.append(
                    SensorReading(
                        machine_id=machine.id,
                        timestamp=row["timestamp"],
                        vibration_rms=row["vibration_rms"],
                        temperature=row["temperature"],
                        rpm=row["rpm"],
                        load_pct=row["load_pct"],
                        pressure=row["pressure"],
                        source=ReadingSource.simulated,
                    )
                )
        db.add_all(readings)
        db.flush()
        events_created = 0
        for reading in readings:
            events_created += len(detection_service.process_reading(db, reading))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "A concurrent simulation wrote these timestamps — retry the request"
        ) from exc
    except Exception:
        db.rollback()
        raise

    return DemoGenerateResponse(
        machines_processed=len(targets),
        readings_created=len(readings),
        anomaly_events_created=events_created,
        skipped_inactive=skipped,
    )
