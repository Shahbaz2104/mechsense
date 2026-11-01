"""CSV import schemas: preview, validation report, job history."""

import enum
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ImportJobStatus(enum.StrEnum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class ImportPreviewResponse(BaseModel):
    """Headers + sample rows + best-guess mapping so the UI can render step 2."""

    filename: str
    size_bytes: int
    headers: list[str]
    row_count: int
    sample_rows: list[dict[str, str]]  # raw cell values, first 5 data rows
    # target field -> suggested input column (None when no candidate found)
    mapping_candidates: dict[str, str | None]


class ImportRowError(BaseModel):
    """One rejected row. `row` is the 1-based file line number (header = 1)."""

    row: int
    field: str | None = None
    message: str


class ImportReport(BaseModel):
    """Validation outcome — returned for dry runs and real imports alike."""

    dry_run: bool
    filename: str
    total_rows: int
    accepted_rows: int
    rejected_rows: int
    errors: list[ImportRowError] = Field(default_factory=list)  # capped at 200
    errors_truncated: bool = False
    job_id: int | None = None  # set only for real imports


class ImportJobRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    identifier: str
    name: str


class ImportJobRead(BaseModel):
    id: int
    filename: str
    machine: ImportJobRef | None = None
    status: ImportJobStatus
    total_rows: int
    accepted_rows: int
    rejected_rows: int
    created_at: datetime
    completed_at: datetime | None = None


class ImportJobDetail(ImportJobRead):
    """History entry with the mapping used and row-level errors for review."""

    column_mapping: dict[str, str] | None = None
    errors: list[ImportRowError] = Field(default_factory=list)
    errors_truncated: bool = False
