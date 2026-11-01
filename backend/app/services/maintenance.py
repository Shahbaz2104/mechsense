"""Work-order business rules: creation, lifecycle, anomaly linking.

Lifecycle (acknowledgment-style explicitness): completed/cancelled are
terminal — any further transition is 409 invalid_state; repeating the current
status is an idempotent update, mirroring anomaly resolve.
"""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError, NotFoundError, ValidationProblem
from app.models import (
    AnomalyEvent,
    Machine,
    MaintenancePriority,
    MaintenanceType,
    MaintenanceWorkOrder,
    WorkOrderStatus,
)
from app.repositories import machines as machine_repo
from app.repositories import maintenance as maintenance_repo
from app.schemas.maintenance import WorkOrderCreate, WorkOrderUpdate

_ALLOWED_TRANSITIONS: dict[WorkOrderStatus, set[WorkOrderStatus]] = {
    WorkOrderStatus.scheduled: {
        WorkOrderStatus.in_progress,
        WorkOrderStatus.completed,
        WorkOrderStatus.cancelled,
    },
    WorkOrderStatus.in_progress: {WorkOrderStatus.completed, WorkOrderStatus.cancelled},
    WorkOrderStatus.completed: set(),
    WorkOrderStatus.cancelled: set(),
}


def get_or_404(db: Session, work_order_id: int) -> MaintenanceWorkOrder:
    order = maintenance_repo.get_work_order(db, work_order_id)
    if order is None:
        raise NotFoundError("Work order", work_order_id)
    return order


def _resolve_machine(db: Session, machine_id: int) -> Machine:
    machine = machine_repo.get_machine(db, machine_id)
    if machine is None:
        raise NotFoundError("Machine", machine_id)
    return machine


def _resolve_events(db: Session, event_ids: list[int], machine_id: int) -> list[AnomalyEvent]:
    if not event_ids:
        return []
    unique_ids = list(dict.fromkeys(event_ids))
    events = list(db.scalars(select(AnomalyEvent).where(AnomalyEvent.id.in_(unique_ids))).all())
    if len(events) != len(unique_ids):
        found = {event.id for event in events}
        missing = next(needle for needle in unique_ids if needle not in found)
        raise NotFoundError("Anomaly event", missing)
    wrong_machine = next((event for event in events if event.machine_id != machine_id), None)
    if wrong_machine is not None:
        raise ValidationProblem(
            "Anomaly events must belong to the work order's machine",
            details=[
                {
                    "field": "anomaly_event_ids",
                    "message": (
                        f"event {wrong_machine.id} belongs to machine "
                        f"{wrong_machine.machine_id}, not {machine_id}"
                    ),
                }
            ],
        )
    return events


def _apply_status(order: MaintenanceWorkOrder, new_status: WorkOrderStatus) -> None:
    if new_status == order.status:
        return
    if new_status not in _ALLOWED_TRANSITIONS[order.status]:
        raise AppError(
            status_code=409,
            code="invalid_state",
            message=f"A {order.status.value} work order cannot move to {new_status.value}",
        )
    order.status = new_status
    now = datetime.now(UTC)
    if new_status == WorkOrderStatus.in_progress and order.started_at is None:
        order.started_at = now
    if new_status == WorkOrderStatus.completed and order.completed_at is None:
        order.completed_at = now


def _stamp_initial_times(order: MaintenanceWorkOrder) -> None:
    now = datetime.now(UTC)
    if order.status == WorkOrderStatus.in_progress and order.started_at is None:
        order.started_at = now
    if order.status == WorkOrderStatus.completed and order.completed_at is None:
        order.completed_at = now


def create_work_order(db: Session, payload: WorkOrderCreate) -> MaintenanceWorkOrder:
    machine = _resolve_machine(db, payload.machine_id)
    events = _resolve_events(db, payload.anomaly_event_ids, machine.id)
    order = MaintenanceWorkOrder(
        work_order_number=maintenance_repo.next_work_order_number(db),
        machine_id=machine.id,
        title=payload.title,
        description=payload.description,
        maintenance_type=MaintenanceType(payload.maintenance_type.value),
        priority=MaintenancePriority(payload.priority.value),
        status=WorkOrderStatus(payload.status.value),
        scheduled_date=payload.scheduled_date,
        technician=payload.technician,
        findings=payload.findings,
        actions_taken=payload.actions_taken,
    )
    _stamp_initial_times(order)
    order.anomaly_events = events
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def update_work_order(
    db: Session, order: MaintenanceWorkOrder, payload: WorkOrderUpdate
) -> MaintenanceWorkOrder:
    data = payload.model_dump(exclude_unset=True)

    if data.get("machine_id") is not None:
        machine = _resolve_machine(db, data["machine_id"])
        order.machine_id = machine.id
    if data.get("status") is not None:
        _apply_status(order, WorkOrderStatus(data["status"].value))
    for field in (
        "title",
        "description",
        "technician",
        "findings",
        "actions_taken",
        "scheduled_date",
    ):
        if field in data:
            setattr(order, field, data[field])
    for field, enum_cls in (
        ("maintenance_type", MaintenanceType),
        ("priority", MaintenancePriority),
    ):
        if field in data and data[field] is not None:
            setattr(order, field, enum_cls(data[field].value))
    if data.get("anomaly_event_ids") is not None:
        order.anomaly_events = _resolve_events(db, data["anomaly_event_ids"], order.machine_id)

    db.commit()
    db.refresh(order)
    return order
