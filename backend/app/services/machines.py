"""Machine business rules: CRUD, conflicts, health summaries.

Health derivation (single source of truth, used by dashboard AND list):
- inactive machine           -> inactive
- no readings yet            -> no_data
- open critical event        -> critical
- open warning event         -> warning
- latest reading violates    -> warning/critical (from threshold evaluation)
- otherwise                  -> healthy
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.detection.thresholds import evaluate_reading
from app.models import (
    AnomalyEvent,
    AnomalyStatus,
    Machine,
    MachineStatus,
    SensorReading,
)
from app.repositories import anomalies as anomaly_repo
from app.repositories import machines as machine_repo
from app.repositories import readings as reading_repo
from app.schemas.machine import AnomalyBrief, MachineCreate, MachineSummary, MachineUpdate


def compute_health(
    machine: Machine,
    latest: SensorReading | None,
    open_severity: str | None,
) -> str:
    if machine.status == MachineStatus.inactive:
        return "inactive"
    if latest is None:
        return "no_data"
    if open_severity is not None:
        return open_severity
    violations = evaluate_reading(latest, machine.thresholds or {})
    if any(v.severity == "critical" for v in violations):
        return "critical"
    if violations:
        return "warning"
    return "healthy"


def summarize_machines(db: Session, machines: list[Machine]) -> list[MachineSummary]:
    """Batch-enrich machines with health/latest context (no N+1)."""
    ids = [m.id for m in machines]
    latest_by_machine = reading_repo.latest_per_machine(db, ids)
    latest_anomaly_by_machine = anomaly_repo.latest_per_machine(db)

    open_severity: dict[int, str] = {}
    open_count: dict[int, int] = {}
    if ids:
        rows = db.execute(
            select(
                AnomalyEvent.machine_id,
                AnomalyEvent.severity,
                func.count(),
            )
            .where(
                AnomalyEvent.machine_id.in_(ids),
                AnomalyEvent.status == AnomalyStatus.open,
            )
            .group_by(AnomalyEvent.machine_id, AnomalyEvent.severity)
        )
        for machine_id, severity, count in rows:
            value = getattr(severity, "value", severity)
            open_count[machine_id] = open_count.get(machine_id, 0) + count
            if value == "critical":
                open_severity[machine_id] = "critical"
            else:
                open_severity.setdefault(machine_id, value)

    summaries: list[MachineSummary] = []
    for machine in machines:
        latest = latest_by_machine.get(machine.id)
        latest_anomaly = latest_anomaly_by_machine.get(machine.id)
        summaries.append(
            MachineSummary(
                id=machine.id,
                identifier=machine.identifier,
                name=machine.name,
                equipment_type=machine.equipment_type,
                status=machine.status,
                health_status=compute_health(machine, latest, open_severity.get(machine.id)),
                latest_reading_at=latest.timestamp if latest else None,
                vibration_rms=float(latest.vibration_rms) if latest else None,
                temperature=float(latest.temperature) if latest else None,
                latest_anomaly=(
                    AnomalyBrief(
                        id=latest_anomaly.id,
                        metric=latest_anomaly.metric,
                        severity=latest_anomaly.severity.value,
                        detected_at=latest_anomaly.detected_at,
                        status=latest_anomaly.status.value,
                    )
                    if latest_anomaly
                    else None
                ),
                open_anomaly_count=open_count.get(machine.id, 0),
            )
        )
    return summaries


def get_machine_or_404(db: Session, machine_id: int) -> Machine:
    machine = machine_repo.get_machine(db, machine_id)
    if machine is None:
        raise NotFoundError("Machine", machine_id)
    return machine


def create_machine(db: Session, payload: MachineCreate) -> Machine:
    if machine_repo.get_by_identifier(db, payload.identifier) is not None:
        raise ConflictError(f"A machine with identifier '{payload.identifier}' already exists")

    machine = Machine(
        identifier=payload.identifier,
        name=payload.name,
        equipment_type=payload.equipment_type.value,
        location=payload.location,
        manufacturer=payload.manufacturer,
        model=payload.model,
        installation_date=payload.installation_date,
        description=payload.description,
        thresholds=payload.thresholds.as_storage(),
        status=MachineStatus.active,
    )
    db.add(machine)
    db.commit()
    db.refresh(machine)
    return machine


def update_machine(db: Session, machine: Machine, payload: MachineUpdate) -> Machine:
    data = payload.model_dump(exclude_unset=True)

    if "thresholds" in data:
        thresholds = payload.thresholds
        machine.thresholds = thresholds.as_storage() if thresholds else {}
        data.pop("thresholds")

    if "identifier" in data:
        new_identifier = data.pop("identifier")
        if new_identifier and new_identifier != machine.identifier:
            existing = machine_repo.get_by_identifier(db, new_identifier)
            if existing is not None and existing.id != machine.id:
                raise ConflictError(f"A machine with identifier '{new_identifier}' already exists")
            machine.identifier = new_identifier

    if "equipment_type" in data:
        equipment_type = data.pop("equipment_type")
        if equipment_type is not None:
            machine.equipment_type = equipment_type.value

    if "status" in data:
        status = data.pop("status")
        if status is not None:
            # Deactivation keeps all historical readings, events and work orders.
            machine.status = MachineStatus(status.value if hasattr(status, "value") else status)

    for field_name, value in data.items():
        if value is not None or field_name in (
            "location",
            "manufacturer",
            "model",
            "description",
            "installation_date",
        ):
            setattr(machine, field_name, value)

    db.commit()
    db.refresh(machine)
    return machine
