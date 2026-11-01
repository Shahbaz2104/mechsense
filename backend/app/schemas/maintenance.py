"""Maintenance work-order schemas (CRUD, filters, lifecycle)."""

import enum
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MaintenanceType(enum.StrEnum):
    preventive = "preventive"
    corrective = "corrective"
    inspection = "inspection"
    other = "other"


class MaintenancePriority(enum.StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class WorkOrderStatus(enum.StrEnum):
    scheduled = "scheduled"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class WorkOrderMachineRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    identifier: str
    name: str


class LinkedAnomalyRef(BaseModel):
    """Summary of an anomaly event linked to a work order."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    metric: str
    severity: str
    status: str
    detected_at: datetime

    @field_validator("severity", "status", mode="before")
    @classmethod
    def _enum_value(cls, value: object) -> object:
        return value.value if isinstance(value, enum.Enum) else value


class WorkOrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    work_order_number: str
    machine: WorkOrderMachineRef
    title: str
    description: str | None = None
    maintenance_type: MaintenanceType
    priority: MaintenancePriority
    status: WorkOrderStatus
    scheduled_date: date | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    technician: str | None = None
    findings: str | None = None
    actions_taken: str | None = None
    anomaly_events: list[LinkedAnomalyRef] = []
    created_at: datetime
    updated_at: datetime

    @field_validator("maintenance_type", "priority", "status", mode="before")
    @classmethod
    def _enum_value(cls, value: object) -> object:
        return value.value if isinstance(value, enum.Enum) else value


class WorkOrderCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    machine_id: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    maintenance_type: MaintenanceType = MaintenanceType.preventive
    priority: MaintenancePriority = MaintenancePriority.medium
    status: WorkOrderStatus = WorkOrderStatus.scheduled
    scheduled_date: date | None = None
    technician: str | None = Field(default=None, max_length=80)
    findings: str | None = Field(default=None, max_length=4000)
    actions_taken: str | None = Field(default=None, max_length=4000)
    anomaly_event_ids: list[int] = Field(default_factory=list, max_length=50)


class WorkOrderUpdate(BaseModel):
    """Partial update: absent fields keep current values. Lifecycle moves
    (status changes) are validated by the service with 409 invalid_state."""

    model_config = ConfigDict(str_strip_whitespace=True)

    machine_id: int | None = Field(default=None, ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    maintenance_type: MaintenanceType | None = None
    priority: MaintenancePriority | None = None
    status: WorkOrderStatus | None = None
    scheduled_date: date | None = None
    technician: str | None = Field(default=None, max_length=80)
    findings: str | None = Field(default=None, max_length=4000)
    actions_taken: str | None = Field(default=None, max_length=4000)
    anomaly_event_ids: list[int] | None = Field(default=None, max_length=50)
