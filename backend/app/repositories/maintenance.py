"""Work-order queries."""

from datetime import date, timedelta

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.models import MaintenanceWorkOrder, WorkOrderStatus

_SORT_COLUMNS = {
    "scheduled_date": MaintenanceWorkOrder.scheduled_date,
    "priority": MaintenanceWorkOrder.priority,
    "status": MaintenanceWorkOrder.status,
    "created_at": MaintenanceWorkOrder.created_at,
    "title": MaintenanceWorkOrder.title,
}


def get_work_order(db: Session, work_order_id: int) -> MaintenanceWorkOrder | None:
    return db.get(MaintenanceWorkOrder, work_order_id)


def _filtered(db: Session, *, filters: dict) -> tuple[Select, int]:
    stmt = select(MaintenanceWorkOrder)
    if filters.get("machine_id") is not None:
        stmt = stmt.where(MaintenanceWorkOrder.machine_id == filters["machine_id"])
    if filters.get("status"):
        stmt = stmt.where(MaintenanceWorkOrder.status == filters["status"])
    if filters.get("priority"):
        stmt = stmt.where(MaintenanceWorkOrder.priority == filters["priority"])
    if filters.get("maintenance_type"):
        stmt = stmt.where(MaintenanceWorkOrder.maintenance_type == filters["maintenance_type"])
    if filters.get("overdue"):
        stmt = stmt.where(
            MaintenanceWorkOrder.status.in_(
                [WorkOrderStatus.scheduled, WorkOrderStatus.in_progress]
            ),
            MaintenanceWorkOrder.scheduled_date < date.today(),
        )
    if filters.get("upcoming"):
        today = date.today()
        stmt = stmt.where(
            MaintenanceWorkOrder.status == WorkOrderStatus.scheduled,
            MaintenanceWorkOrder.scheduled_date >= today,
            MaintenanceWorkOrder.scheduled_date <= today + timedelta(days=7),
        )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    return stmt, int(total)


def list_work_orders(
    db: Session,
    *,
    machine_id: int | None = None,
    status: str | None = None,
    priority: str | None = None,
    maintenance_type: str | None = None,
    overdue: bool = False,
    upcoming: bool = False,
    sort: str = "scheduled_date",
    descending: bool = False,
    offset: int = 0,
    limit: int = 25,
) -> tuple[list[MaintenanceWorkOrder], int]:
    stmt, total = _filtered(
        db,
        filters={
            "machine_id": machine_id,
            "status": status,
            "priority": priority,
            "maintenance_type": maintenance_type,
            "overdue": overdue,
            "upcoming": upcoming,
        },
    )
    primary = _SORT_COLUMNS[sort]
    primary_order = primary.desc() if descending else primary.asc()
    stmt = (
        stmt.options(selectinload(MaintenanceWorkOrder.machine))
        .order_by(primary_order, MaintenanceWorkOrder.id.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = db.scalars(stmt).all()
    return list(rows), total


def next_work_order_number(db: Session) -> str:
    """WO-0001 style numbering; work orders are never deleted so count+1 is stable."""
    count = db.scalar(select(func.count()).select_from(MaintenanceWorkOrder)) or 0
    return f"WO-{count + 1:04d}"
