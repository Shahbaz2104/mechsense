"""Dashboard aggregation — every figure comes from persisted data.

Health derivation per machine:
- inactive machine           -> inactive
- no readings yet            -> no_data
- open critical event        -> critical
- open warning event         -> warning
- latest reading violates    -> warning/critical (from threshold evaluation)
- otherwise                  -> healthy
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    AnomalyEvent,
    DataImportJob,
    Machine,
    MachineStatus,
    MaintenanceWorkOrder,
    WorkOrderStatus,
)
from app.repositories import anomalies as anomaly_repo
from app.schemas.dashboard import (
    ActivityItem,
    ActivityKind,
    ActivityResponse,
    DashboardResponse,
    DashboardSummary,
    PeriodCount,
)
from app.services.machines import summarize_machines

_PERIODS: dict[str, timedelta] = {
    "1h": timedelta(hours=1),
    "6h": timedelta(hours=6),
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}


def period_window(period: str) -> tuple[datetime, datetime, datetime, datetime]:
    """Return (current_start, current_end, previous_start, previous_end) in UTC."""
    delta = _PERIODS.get(period, _PERIODS["7d"])
    now = datetime.now(UTC)
    current_start = now - delta
    previous_start = current_start - delta
    return current_start, now, previous_start, current_start


def build_dashboard(db: Session, period: str = "7d") -> DashboardResponse:
    now = datetime.now(UTC)
    current_start, current_end, previous_start, previous_end = period_window(period)

    machines = list(db.scalars(select(Machine).order_by(Machine.name)).all())
    summaries = summarize_machines(db, machines)

    total = len(machines)
    inactive = sum(1 for m in machines if m.status == MachineStatus.inactive)
    active = total - inactive
    attention = sum(1 for s in summaries if s.health_status in ("warning", "critical"))
    healthy = sum(1 for s in summaries if s.health_status == "healthy")

    active_alerts = anomaly_repo.open_alert_count(db)
    current_count = anomaly_repo.count_period(db, start=current_start, end=current_end)
    previous_count = anomaly_repo.count_period(db, start=previous_start, end=previous_end)

    today = now.date()
    week_ahead = (now + timedelta(days=7)).date()
    overdue = int(
        db.scalar(
            select(func.count())
            .select_from(MaintenanceWorkOrder)
            .where(
                MaintenanceWorkOrder.status.in_(
                    [WorkOrderStatus.scheduled, WorkOrderStatus.in_progress]
                ),
                MaintenanceWorkOrder.scheduled_date < today,
            )
        )
        or 0
    )
    upcoming = int(
        db.scalar(
            select(func.count())
            .select_from(MaintenanceWorkOrder)
            .where(
                MaintenanceWorkOrder.status == WorkOrderStatus.scheduled,
                MaintenanceWorkOrder.scheduled_date >= today,
                MaintenanceWorkOrder.scheduled_date <= week_ahead,
            )
        )
        or 0
    )

    summary = DashboardSummary(
        total_machines=total,
        active_machines=active,
        healthy_machines=healthy,
        attention_machines=attention,
        inactive_machines=inactive,
        active_alerts=active_alerts,
        anomalies_period=PeriodCount(
            current=current_count,
            previous=previous_count,
            period_start=current_start,
            period_end=current_end,
        ),
        overdue_work_orders=overdue,
        upcoming_work_orders=upcoming,
        generated_at=now,
    )
    return DashboardResponse(summary=summary, machines=summaries)


def build_activity(db: Session, limit: int = 10) -> ActivityResponse:
    """Latest operational events: imports, detected anomalies, acknowledgments,
    resolutions, and work orders. Every item traces to a persisted row."""
    now = datetime.now(UTC)
    items: list[ActivityItem] = []

    events = db.scalars(
        select(AnomalyEvent)
        .options(selectinload(AnomalyEvent.machine))
        .order_by(AnomalyEvent.detected_at.desc())
        .limit(limit)
    ).all()
    for event in events:
        machine = event.machine
        base = {
            "machine_id": machine.id if machine else None,
            "machine_identifier": machine.identifier if machine else None,
            "entity_id": event.id,
        }
        metric = event.metric.replace("_", " ")
        items.append(
            ActivityItem(
                id=f"anomaly:{event.id}",
                kind=ActivityKind.anomaly,
                title=f"{event.severity.value} {metric} on {machine.identifier}",
                detail=event.explanation,
                occurred_at=event.detected_at,
                **base,
            )
        )
        if event.acknowledged_at is not None:
            items.append(
                ActivityItem(
                    id=f"ack:{event.id}",
                    kind=ActivityKind.acknowledged,
                    title=f"Acknowledged {metric} alert on {machine.identifier}",
                    detail=event.notes,
                    occurred_at=event.acknowledged_at,
                    **base,
                )
            )
        if event.resolved_at is not None:
            items.append(
                ActivityItem(
                    id=f"resolve:{event.id}",
                    kind=ActivityKind.resolved,
                    title=f"Resolved {metric} alert on {machine.identifier}",
                    detail=event.notes,
                    occurred_at=event.resolved_at,
                    **base,
                )
            )

    imports = db.execute(
        select(DataImportJob, Machine.identifier)
        .join(Machine, DataImportJob.machine_id == Machine.id, isouter=True)
        .order_by(DataImportJob.created_at.desc())
        .limit(limit)
    ).all()
    for job, identifier in imports:
        items.append(
            ActivityItem(
                id=f"import:{job.id}",
                kind=ActivityKind.import_,
                title=f"Imported {job.filename}",
                detail=f"{job.accepted_rows} of {job.total_rows} rows accepted",
                occurred_at=job.created_at,
                machine_id=job.machine_id,
                machine_identifier=identifier,
                entity_id=job.id,
            )
        )

    orders = db.scalars(
        select(MaintenanceWorkOrder).order_by(MaintenanceWorkOrder.created_at.desc()).limit(limit)
    ).all()
    for order in orders:
        machine = order.machine
        items.append(
            ActivityItem(
                id=f"work_order:{order.id}",
                kind=ActivityKind.work_order,
                title=f"Work order {order.work_order_number} created",
                detail=order.title,
                occurred_at=order.created_at,
                machine_id=machine.id if machine else None,
                machine_identifier=machine.identifier if machine else None,
                entity_id=order.id,
            )
        )
        if order.completed_at is not None:
            items.append(
                ActivityItem(
                    id=f"work_order_done:{order.id}",
                    kind=ActivityKind.work_order,
                    title=f"Work order {order.work_order_number} completed",
                    detail=order.title,
                    occurred_at=order.completed_at,
                    machine_id=machine.id if machine else None,
                    machine_identifier=machine.identifier if machine else None,
                    entity_id=order.id,
                )
            )

    items.sort(key=lambda item: item.occurred_at, reverse=True)
    return ActivityResponse(items=items[:limit], generated_at=now)
