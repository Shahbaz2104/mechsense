"""Idempotent demo seed: machines, history, detection, maintenance records.

Safe to re-run: existing machines are reused, machines that already have
readings are skipped, and work-order numbers are only created when missing.
`force=True` clears generated data (readings, events, work orders, detection
runs) and rebuilds it — machine definitions are preserved.
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.detection import service as detection_service
from app.models import (
    AnomalyEvent,
    AnomalyStatus,
    DetectionRun,
    Machine,
    MachineStatus,
    MaintenancePriority,
    MaintenanceType,
    MaintenanceWorkOrder,
    ReadingSource,
    SensorReading,
    WorkOrderStatus,
    work_order_anomaly_events,
)
from app.simulation import generator

logger = logging.getLogger("mechsense.seed")

READ_INTERVAL = generator.READ_INTERVAL
HISTORY_DAYS = 7


@dataclass(frozen=True)
class MachineSpec:
    identifier: str
    name: str
    equipment_type: str
    location: str
    manufacturer: str
    model: str
    installed: date
    description: str
    thresholds: dict
    has_pressure: bool


DEMO_MACHINES: tuple[MachineSpec, ...] = (
    MachineSpec(
        identifier="P-101",
        name="Centrifugal Pump P-101",
        equipment_type="pump",
        location="Process Hall A — Cooling Water Loop",
        manufacturer="Flowserve",
        model="D-155M",
        installed=date(2021, 4, 12),
        description=(
            "Primary cooling-water circulation pump. Simulated demo asset — "
            "thresholds are illustrative configuration values, not safety limits."
        ),
        thresholds={
            "vibration_rms": {"warning": 4.5, "critical": 7.1},
            "temperature": {"warning": 75.0, "critical": 90.0},
        },
        has_pressure=False,
    ),
    MachineSpec(
        identifier="M-204",
        name="Electric Motor M-204",
        equipment_type="motor",
        location="Process Hall A — Conveyor Drive",
        manufacturer="Siemens",
        model="1LE0 203-1",
        installed=date(2020, 9, 3),
        description=("460 V induction motor driving the main conveyor. Simulated demo asset."),
        thresholds={
            "vibration_rms": {"warning": 4.5, "critical": 7.1},
            "temperature": {"warning": 80.0, "critical": 95.0},
        },
        has_pressure=False,
    ),
    MachineSpec(
        identifier="F-301",
        name="Industrial Fan F-301",
        equipment_type="fan",
        location="Roof Plant — Extraction Fan 3",
        manufacturer="New York Blower",
        model="CSIW 355",
        installed=date(2019, 6, 20),
        description=(
            "Roof-mounted extraction fan, healthy baseline reference. Simulated demo asset."
        ),
        thresholds={
            "vibration_rms": {"warning": 5.0, "critical": 8.0},
            "temperature": {"warning": 75.0, "critical": 90.0},
        },
        has_pressure=False,
    ),
    MachineSpec(
        identifier="C-401",
        name="Compressor C-401",
        equipment_type="compressor",
        location="Utility Basement — Air Header",
        manufacturer="Atlas Copco",
        model="GA 75 VSD+",
        installed=date(2022, 2, 14),
        description=("Rotary screw compressor serving the plant air header. Simulated demo asset."),
        thresholds={
            "vibration_rms": {"warning": 5.0, "critical": 8.0},
            "temperature": {"warning": 80.0, "critical": 95.0},
            "pressure": {"warning": 9.0, "critical": 11.0},
        },
        has_pressure=True,
    ),
    MachineSpec(
        identifier="B-501",
        name="Bearing Assembly B-501",
        equipment_type="bearing",
        location="Line 2 — Idler Station",
        manufacturer="SKF",
        model="SAF 22218",
        installed=date(2023, 11, 7),
        description=(
            "Spherical roller bearing assembly on conveyor idler station. Simulated demo asset."
        ),
        thresholds={
            "vibration_rms": {"warning": 4.0, "critical": 6.5},
            "temperature": {"warning": 70.0, "critical": 85.0},
        },
        has_pressure=False,
    ),
)


@dataclass
class SeedResult:
    machines_created: int = 0
    machines_reused: int = 0
    readings_created: int = 0
    machines_skipped: list[str] = field(default_factory=list)
    events_created: int = 0
    work_orders_created: int = 0
    forced: bool = False


def _history_window(anchor: datetime) -> tuple[datetime, datetime]:
    end = anchor.replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(days=HISTORY_DAYS)
    return start, end


def _clear_generated_data(db: Session) -> None:
    db.execute(delete(work_order_anomaly_events))
    db.execute(delete(AnomalyEvent))
    db.execute(delete(SensorReading))
    db.execute(delete(MaintenanceWorkOrder))
    db.execute(delete(DetectionRun))
    db.commit()


def seed_demo_data(
    db: Session, *, force: bool = False, anchor: datetime | None = None
) -> SeedResult:
    settings = get_settings()
    anchor = anchor or datetime.now(UTC)
    if anchor.tzinfo is None:
        anchor = anchor.replace(tzinfo=UTC)

    result = SeedResult(forced=force)
    if force:
        _clear_generated_data(db)
        result.forced = True

    start, end = _history_window(anchor)

    for index, spec in enumerate(DEMO_MACHINES):
        machine = db.scalar(select(Machine).where(Machine.identifier == spec.identifier))
        if machine is None:
            machine = Machine(
                identifier=spec.identifier,
                name=spec.name,
                equipment_type=spec.equipment_type,
                location=spec.location,
                manufacturer=spec.manufacturer,
                model=spec.model,
                installation_date=spec.installed,
                description=spec.description,
                thresholds=spec.thresholds,
                status=MachineStatus.active,
            )
            db.add(machine)
            db.flush()
            result.machines_created += 1
        else:
            result.machines_reused += 1

        existing_count = db.scalar(
            select(SensorReading.id).where(SensorReading.machine_id == machine.id).limit(1)
        )
        if existing_count is not None:
            result.machines_skipped.append(spec.identifier)
            continue

        profile = generator.profile_for(spec.identifier)
        rows = generator.generate_history(
            profile,
            machine_identifier=spec.identifier,
            base_seed=settings.simulation_seed + index,
            start=start,
            end=end,
            interval=READ_INTERVAL,
            has_pressure=spec.has_pressure,
        )
        readings = [
            SensorReading(
                machine_id=machine.id,
                timestamp=row["timestamp"],
                vibration_rms=Decimal(str(row["vibration_rms"])),
                temperature=Decimal(str(row["temperature"])),
                rpm=Decimal(str(row["rpm"])),
                load_pct=Decimal(str(row["load_pct"])),
                pressure=Decimal(str(row["pressure"])) if row["pressure"] is not None else None,
                source=ReadingSource.simulated,
            )
            for row in rows
        ]
        db.add_all(readings)
        db.flush()
        result.readings_created += len(readings)

        # Run threshold detection exactly as live ingestion does.
        for reading in readings:
            detection_service.process_reading(db, reading)
        db.flush()

    _seed_work_orders(db, result)
    _record_detection_run(db, result)
    db.commit()
    return result


def _seed_work_orders(db: Session, result: SeedResult) -> None:
    """Demo maintenance records — one completed, one overdue, one upcoming."""
    existing = db.scalar(
        select(MaintenanceWorkOrder.id).where(MaintenanceWorkOrder.work_order_number == "WO-0001")
    )
    if existing is not None:
        return

    pump = db.scalar(select(Machine).where(Machine.identifier == "P-101"))
    motor = db.scalar(select(Machine).where(Machine.identifier == "M-204"))
    bearing = db.scalar(select(Machine).where(Machine.identifier == "B-501"))
    if pump is None or motor is None or bearing is None:
        return

    anchor_date = datetime.now(UTC).date()

    completed = MaintenanceWorkOrder(
        work_order_number="WO-0001",
        machine_id=bearing.id,
        title="Re-lubricate idler bearing B-501",
        description="Routine lubrication round on Line 2 idler stations.",
        maintenance_type=MaintenanceType.preventive,
        priority=MaintenancePriority.medium,
        status=WorkOrderStatus.completed,
        scheduled_date=anchor_date - timedelta(days=5),
        started_at=_days_ago_utc(5, hour=8),
        completed_at=_days_ago_utc(5, hour=10),
        technician="R. Alvarez",
        findings="Grease contaminated with fines; no play in housing.",
        actions_taken="Purged and re-greased with lithium complex EP2.",
    )
    overdue = MaintenanceWorkOrder(
        work_order_number="WO-0002",
        machine_id=motor.id,
        title="Inspect M-204 coupling alignment",
        description="Post-shutdown alignment verification (soft foot check).",
        maintenance_type=MaintenanceType.inspection,
        priority=MaintenancePriority.high,
        status=WorkOrderStatus.scheduled,
        scheduled_date=anchor_date - timedelta(days=2),
        technician="T. Okafor",
    )
    upcoming = MaintenanceWorkOrder(
        work_order_number="WO-0003",
        machine_id=pump.id,
        title="Investigate rising vibration on P-101",
        description=(
            "Check bearing condition, coupling and impeller balance after "
            "warning/critical vibration events."
        ),
        maintenance_type=MaintenanceType.corrective,
        priority=MaintenancePriority.urgent,
        status=WorkOrderStatus.scheduled,
        scheduled_date=anchor_date + timedelta(days=2),
        technician="R. Alvarez",
    )
    db.add_all([completed, overdue, upcoming])
    db.flush()

    # Link the pump's active bearing-fault events to the corrective work order.
    pump_events = db.scalars(
        select(AnomalyEvent)
        .where(
            AnomalyEvent.machine_id == pump.id,
            AnomalyEvent.status != AnomalyStatus.resolved,
        )
        .order_by(AnomalyEvent.detected_at)
    ).all()
    upcoming.anomaly_events = list(pump_events)
    result.work_orders_created = 3


def _days_ago_utc(days: int, hour: int = 0) -> datetime:
    day = datetime.now(UTC).date() - timedelta(days=days)
    return datetime.combine(day, time(hour=hour), tzinfo=UTC)


def _record_detection_run(db: Session, result: SeedResult) -> None:
    if result.readings_created == 0 and not result.forced:
        return
    readings_count = int(db.scalar(select(func.count()).select_from(SensorReading)) or 0)
    events_count = int(db.scalar(select(func.count()).select_from(AnomalyEvent)) or 0)
    db.add(
        DetectionRun(
            method="threshold",
            finished_at=datetime.now(UTC),
            readings_processed=readings_count,
            events_created=events_count,
            parameters={"seed": get_settings().simulation_seed, "interval_minutes": 5},
            notes="Initial seed pipeline run over generated demo history.",
        )
    )
