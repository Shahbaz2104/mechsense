"""Dashboard summary schema — every number is computed from persisted data."""

import enum
from datetime import datetime

from pydantic import BaseModel

from app.schemas.machine import MachineSummary


class PeriodCount(BaseModel):
    """Count of events in the selected period with the previous period for context."""

    current: int
    previous: int
    period_start: datetime
    period_end: datetime


class DashboardSummary(BaseModel):
    total_machines: int
    active_machines: int
    healthy_machines: int
    attention_machines: int  # machines with warning/critical health
    inactive_machines: int
    # Unacknowledged open events = actionable alerts.
    active_alerts: int
    anomalies_period: PeriodCount
    overdue_work_orders: int
    upcoming_work_orders: int
    generated_at: datetime


class DashboardResponse(BaseModel):
    summary: DashboardSummary
    machines: list[MachineSummary]


class ActivityKind(enum.StrEnum):
    """Categories shown in the latest-activity feed (spec §5E)."""

    anomaly = "anomaly"
    acknowledged = "acknowledged"
    resolved = "resolved"
    import_ = "import"
    work_order = "work_order"


class ActivityItem(BaseModel):
    """One real operational event — never synthesized."""

    id: str  # stable key, e.g. "anomaly:12"
    kind: ActivityKind
    title: str
    detail: str | None = None
    occurred_at: datetime
    machine_id: int | None = None
    machine_identifier: str | None = None
    entity_id: int | None = None  # event / work order / import job id


class ActivityResponse(BaseModel):
    items: list[ActivityItem]
    generated_at: datetime
