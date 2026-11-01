"""Machine (asset) registry."""

import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MachineStatus(enum.StrEnum):
    active = "active"
    inactive = "inactive"


class Machine(Base):
    __tablename__ = "machines"

    id: Mapped[int] = mapped_column(primary_key=True)
    identifier: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    equipment_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    location: Mapped[str | None] = mapped_column(String(120))
    manufacturer: Mapped[str | None] = mapped_column(String(120))
    model: Mapped[str | None] = mapped_column(String(120))
    installation_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[MachineStatus] = mapped_column(
        Enum(MachineStatus, name="machine_status", native_enum=True),
        default=MachineStatus.active,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text)
    # Per-sensor thresholds: {"vibration_rms": {"warning": 4.5, "critical": 7.1}, ...}
    thresholds: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Heavy collections raise on access: always query them explicitly with
    # limits (prevents accidental unbounded loads and N+1 query patterns).
    readings: Mapped[list["SensorReading"]] = relationship(  # noqa: F821
        back_populates="machine",
        lazy="raise",
    )
    anomaly_events: Mapped[list["AnomalyEvent"]] = relationship(  # noqa: F821
        back_populates="machine",
        lazy="raise",
    )
    work_orders: Mapped[list["MaintenanceWorkOrder"]] = relationship(  # noqa: F821
        back_populates="machine",
        lazy="raise",
    )
