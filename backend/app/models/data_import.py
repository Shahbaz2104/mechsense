"""CSV import job records (audit trail for uploaded datasets)."""

import enum
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ImportStatus(enum.StrEnum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class DataImportJob(Base):
    __tablename__ = "data_import_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    machine_id: Mapped[int | None] = mapped_column(
        ForeignKey("machines.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[ImportStatus] = mapped_column(
        Enum(ImportStatus, name="import_status", native_enum=True),
        default=ImportStatus.pending,
        nullable=False,
    )
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    accepted_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rejected_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Column mapping used for the import, e.g. {"ts": "timestamp", "vib": "vibration_rms"}.
    column_mapping: Mapped[dict | None] = mapped_column(JSONB)
    # Row-level validation problems: [{"row": 12, "field": "timestamp", "message": "..."}]
    errors: Mapped[list | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
