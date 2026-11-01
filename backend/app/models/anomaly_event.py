"""Anomaly events produced by the detection engines."""

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AnomalySeverity(enum.StrEnum):
    warning = "warning"
    critical = "critical"


class AnomalyMethod(enum.StrEnum):
    threshold = "threshold"
    statistical = "statistical"


class AnomalyStatus(enum.StrEnum):
    open = "open"
    acknowledged = "acknowledged"
    resolved = "resolved"


class AnomalyEvent(Base):
    """One detection event.

    Lifecycle: open -> acknowledged -> resolved (acknowledgment != resolution).
    Deduplication: at most one active (open/acknowledged) event per
    (machine, metric, method); see app/detection/service.py for the strategy.
    """

    __tablename__ = "anomaly_events"
    __table_args__ = (
        Index("ix_anomaly_events_machine_detected", "machine_id", "detected_at"),
        Index("ix_anomaly_events_status_severity", "status", "severity"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    machine_id: Mapped[int] = mapped_column(
        ForeignKey("machines.id", ondelete="RESTRICT"), nullable=False
    )
    reading_id: Mapped[int] = mapped_column(
        ForeignKey("sensor_readings.id", ondelete="RESTRICT"), nullable=False
    )
    metric: Mapped[str] = mapped_column(String(32), nullable=False)
    observed_value: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    # Threshold value or statistical baseline that triggered the event (NULL if n/a).
    threshold_value: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    severity: Mapped[AnomalySeverity] = mapped_column(
        Enum(AnomalySeverity, name="anomaly_severity", native_enum=True),
        nullable=False,
    )
    method: Mapped[AnomalyMethod] = mapped_column(
        Enum(AnomalyMethod, name="anomaly_method", native_enum=True),
        nullable=False,
    )
    status: Mapped[AnomalyStatus] = mapped_column(
        Enum(AnomalyStatus, name="anomaly_status", native_enum=True),
        default=AnomalyStatus.open,
        nullable=False,
    )
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Updated while the condition keeps triggering (event grouping window).
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Human-readable explanation, e.g.
    # "Warning: vibration RMS reached 7.2 mm/s against the configured warning
    # threshold of 4.5 mm/s."
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    machine: Mapped["Machine"] = relationship(  # noqa: F821
        back_populates="anomaly_events", lazy="selectin"
    )
    # Loaded explicitly (selectinload) on detail views only — never per-row in lists.
    reading: Mapped["SensorReading"] = relationship(  # noqa: F821
        lazy="raise",
    )
