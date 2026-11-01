"""Machine repository: filtering, sorting, pagination queries."""

from sqlalchemy import and_, case, exists, func, or_, select, true
from sqlalchemy.orm import Session

from app.detection.thresholds import THRESHOLD_METRICS
from app.models import AnomalyEvent, AnomalyStatus, Machine, MachineStatus, SensorReading

_SORTABLE = {
    "name": Machine.name,
    "identifier": Machine.identifier,
    "equipment_type": Machine.equipment_type,
    "created_at": Machine.created_at,
    "status": Machine.status,
}

_ACTIVE_STATUSES = [AnomalyStatus.open]  # health uses OPEN events (matches compute_health)


def get_machine(db: Session, machine_id: int) -> Machine | None:
    return db.get(Machine, machine_id)


def get_by_identifier(db: Session, identifier: str) -> Machine | None:
    return db.scalar(select(Machine).where(Machine.identifier == identifier))


def _open_event_exists(severity: str) -> bool:
    return exists(
        select(AnomalyEvent.id).where(
            AnomalyEvent.machine_id == Machine.id,
            AnomalyEvent.status.in_(_ACTIVE_STATUSES),
            AnomalyEvent.severity == severity,
        )
    )


def _threshold_violation(metric: str, column, level: str):
    threshold = Machine.thresholds[metric][level].as_float()
    return and_(column.isnot(None), threshold.isnot(None), column >= threshold)


def list_machines(
    db: Session,
    *,
    search: str | None = None,
    equipment_type: str | None = None,
    status: str | None = None,
    health: str | None = None,
    sort: str = "name",
    descending: bool = False,
    offset: int = 0,
    limit: int = 25,
) -> tuple[list[Machine], int]:
    """List machines; `health` filters on derived health (SQL mirror of
    services.machines.compute_health so pagination stays correct)."""
    # LEFT JOIN LATERAL latest reading per machine.
    latest = (
        select(SensorReading)
        .where(SensorReading.machine_id == Machine.id)
        .order_by(SensorReading.timestamp.desc(), SensorReading.id.desc())
        .limit(1)
        .lateral("lr")
    )
    stmt = select(Machine).outerjoin(latest, true())

    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(or_(Machine.name.ilike(pattern), Machine.identifier.ilike(pattern)))
    if equipment_type:
        stmt = stmt.where(Machine.equipment_type == equipment_type)
    if status:
        stmt = stmt.where(Machine.status == MachineStatus(status))

    if health:
        critical_violations = [
            _threshold_violation(metric, latest.c[metric], "critical")
            for metric in THRESHOLD_METRICS
        ]
        warning_violations = [
            _threshold_violation(metric, latest.c[metric], "warning")
            for metric in THRESHOLD_METRICS
        ]
        health_expr = case(
            (Machine.status == MachineStatus.inactive, "inactive"),
            (latest.c.timestamp.is_(None), "no_data"),
            (_open_event_exists("critical"), "critical"),
            (_open_event_exists("warning"), "warning"),
            (or_(*critical_violations), "critical"),
            (or_(*warning_violations), "warning"),
            else_="healthy",
        )
        stmt = stmt.where(health_expr == health)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    order_column = _SORTABLE.get(sort, Machine.name)
    ordering = order_column.desc() if descending else order_column.asc()
    # Stable ordering: always tie-break on primary key.
    rows = db.scalars(stmt.order_by(ordering, Machine.id).offset(offset).limit(limit)).all()
    return list(rows), int(total)
