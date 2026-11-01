"""Time-series sensor measurements."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.schemas.reading import ReadingSource

__all__ = ["ReadingSource", "SensorReading"]


class SensorReading(Base):
    __tablename__ = "sensor_readings"
    __table_args__ = (
        # One reading per machine per timestamp (also powers DISTINCT ON lookups).
        Index("uq_sensor_readings_machine_ts", "machine_id", "timestamp", unique=True),
        Index("ix_sensor_readings_timestamp", "timestamp"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    machine_id: Mapped[int] = mapped_column(
        ForeignKey("machines.id", ondelete="RESTRICT"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Units: vibration_rms = mm/s (RMS), temperature = degC, rpm = rev/min,
    # load_pct = %, pressure = bar (nullable — not every machine has a sensor).
    vibration_rms: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)
    temperature: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    rpm: Mapped[Decimal] = mapped_column(Numeric(9, 1), nullable=False)
    load_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    pressure: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    source: Mapped[ReadingSource] = mapped_column(
        Enum(ReadingSource, name="reading_source", native_enum=True),
        default=ReadingSource.simulated,
        nullable=False,
    )
    import_job_id: Mapped[int | None] = mapped_column(
        ForeignKey("data_import_jobs.id", ondelete="SET NULL"), nullable=True
    )
    # Quality metadata, e.g. {"flags": ["interpolated"]} or validator notes.
    quality_metadata: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    machine: Mapped["Machine"] = relationship(back_populates="readings", lazy="raise")  # noqa: F821
