"""Record of detector executions (statistical sweeps, seeded runs)."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DetectionRun(Base):
    __tablename__ = "detection_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    method: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    readings_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    events_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    parameters: Mapped[dict | None] = mapped_column(JSONB)
    notes: Mapped[str | None] = mapped_column(String(500))
