"""Maintenance work orders and their links to anomaly events."""

import enum
from datetime import date, datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


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


work_order_anomaly_events = Table(
    "work_order_anomaly_events",
    Base.metadata,
    Column(
        "work_order_id",
        ForeignKey("work_orders.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "anomaly_event_id",
        ForeignKey("anomaly_events.id", ondelete="RESTRICT"),
        primary_key=True,
    ),
)


class MaintenanceWorkOrder(Base):
    __tablename__ = "work_orders"
    __table_args__ = (Index("ix_work_orders_status_scheduled", "status", "scheduled_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    work_order_number: Mapped[str] = mapped_column(String(24), unique=True, nullable=False)
    machine_id: Mapped[int] = mapped_column(
        ForeignKey("machines.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    maintenance_type: Mapped[MaintenanceType] = mapped_column(
        Enum(MaintenanceType, name="maintenance_type", native_enum=True),
        default=MaintenanceType.preventive,
        nullable=False,
    )
    priority: Mapped[MaintenancePriority] = mapped_column(
        Enum(MaintenancePriority, name="maintenance_priority", native_enum=True),
        default=MaintenancePriority.medium,
        nullable=False,
    )
    status: Mapped[WorkOrderStatus] = mapped_column(
        Enum(WorkOrderStatus, name="work_order_status", native_enum=True),
        default=WorkOrderStatus.scheduled,
        nullable=False,
    )
    scheduled_date: Mapped[date | None] = mapped_column(Date)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    technician: Mapped[str | None] = mapped_column(String(80))
    findings: Mapped[str | None] = mapped_column(Text)
    actions_taken: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    machine: Mapped["Machine"] = relationship(  # noqa: F821
        back_populates="work_orders", lazy="selectin"
    )
    anomaly_events: Mapped[list["AnomalyEvent"]] = relationship(  # noqa: F821
        secondary=work_order_anomaly_events,
        lazy="selectin",
    )
