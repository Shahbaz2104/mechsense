"""CSV sensor-import pipeline: parse -> map -> validate -> atomic insert.

Validation is row-level with file line numbers (header = row 1) so the UI can
quote actionable errors back to the engineer. A real import writes job +
accepted readings + detection results in ONE transaction — a failure rolls
everything back (no partial imports). Dry runs touch nothing.

Timestamp convention (documented in the UI): ISO 8601; timezone-aware values
keep their offset, naive values are interpreted as UTC.
"""

import io
import json
from datetime import UTC, datetime
from decimal import Decimal

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import NotFoundError, ValidationProblem
from app.detection import service as detection_service
from app.models import DataImportJob, ImportStatus, Machine, ReadingSource, SensorReading
from app.schemas.data_import import ImportPreviewResponse, ImportReport, ImportRowError

TARGET_FIELDS = ("timestamp", "vibration_rms", "temperature", "rpm", "load_pct", "pressure")
REQUIRED_FIELDS = ("timestamp", "vibration_rms", "temperature", "rpm", "load_pct")

# Inclusive bounds mirroring ReadingCreate — same limits on every ingest path.
_FIELD_BOUNDS: dict[str, tuple[float, float]] = {
    "vibration_rms": (0.0, 500.0),  # mm/s RMS
    "temperature": (-100.0, 1500.0),  # degC
    "rpm": (0.0, 1_000_000.0),  # rev/min
    "load_pct": (0.0, 100.0),  # %
    "pressure": (0.0, 1000.0),  # bar (optional metric)
}

# Header-name synonyms used to guess the mapping during preview.
_HEADER_SYNONYMS: dict[str, tuple[str, ...]] = {
    "timestamp": ("timestamp", "ts", "time", "datetime", "date_time", "when", "utc_time"),
    "vibration_rms": (
        "vibration_rms",
        "vibration",
        "vib",
        "vibration_rms_mm_s",
        "vibration_mm_s",
        "rms",
    ),
    "temperature": ("temperature", "temp", "temperature_c", "temp_c", "degc"),
    "rpm": ("rpm", "speed", "rotational_speed", "rev_min"),
    "load_pct": ("load_pct", "load", "load_percent", "utilization", "capacity"),
    "pressure": ("pressure", "pressure_bar", "bar"),
}

MAX_REPORTED_ERRORS = 200
_DUPLICATE_CHUNK = 10_000
_SAMPLE_ROWS = 5


def _normalize(header: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in header.strip().lower()).strip("_")


def _check_size(raw: bytes) -> None:
    settings = get_settings()
    max_bytes = settings.import_max_file_mb * 1024 * 1024
    if len(raw) > max_bytes:
        raise ValidationProblem(
            f"File is {len(raw) // (1024 * 1024)} MB; the limit is {settings.import_max_file_mb} MB"
        )


def _read_frame(raw: bytes, filename: str) -> pd.DataFrame:
    _check_size(raw)
    if not raw.strip():
        raise ValidationProblem(f"{filename} is empty")
    settings = get_settings()
    try:
        frame = pd.read_csv(io.BytesIO(raw))
    except pd.errors.EmptyDataError as exc:
        raise ValidationProblem(f"{filename} contains no parseable columns") from exc
    except (pd.errors.ParserError, UnicodeDecodeError) as exc:
        raise ValidationProblem(f"{filename} could not be parsed as CSV: {exc}") from exc
    if frame.empty:
        raise ValidationProblem(f"{filename} has headers but no data rows")
    if len(frame) > settings.import_max_rows:
        raise ValidationProblem(
            f"{filename} has {len(frame)} rows; the limit is {settings.import_max_rows}"
        )
    if frame.columns.duplicated().any():
        dupes = sorted({str(c) for c in frame.columns[frame.columns.duplicated()]})
        raise ValidationProblem(f"Duplicate column names: {', '.join(dupes)}")
    return frame


def _mapping_candidates(headers: list[str]) -> dict[str, str | None]:
    normalized = {_normalize(h): h for h in headers}
    candidates: dict[str, str | None] = {}
    for field in TARGET_FIELDS:
        exact = normalized.get(field)
        if exact is not None:
            candidates[field] = exact
            continue
        synonyms = _HEADER_SYNONYMS[field]
        candidates[field] = next((normalized[s] for s in synonyms if s in normalized), None)
    return candidates


def preview_upload(raw: bytes, filename: str) -> ImportPreviewResponse:
    frame = _read_frame(raw, filename)
    headers = [str(col) for col in frame.columns]
    sample = [
        {str(col): "" if pd.isna(value) else str(value) for col, value in row.items()}
        for row in frame.head(_SAMPLE_ROWS).to_dict(orient="records")
    ]
    return ImportPreviewResponse(
        filename=filename,
        size_bytes=len(raw),
        headers=headers,
        row_count=len(frame),
        sample_rows=sample,
        mapping_candidates=_mapping_candidates(headers),
    )


def _parse_mapping(mapping_json: str, headers: list[str]) -> dict[str, str]:
    try:
        raw_mapping = json.loads(mapping_json)
    except json.JSONDecodeError as exc:
        raise ValidationProblem(f"mapping is not valid JSON: {exc}") from exc
    if not isinstance(raw_mapping, dict):
        raise ValidationProblem("mapping must be an object of input column -> field")

    mapping: dict[str, str] = {}
    for input_col, target in raw_mapping.items():
        if input_col not in headers:
            raise ValidationProblem(
                f"mapping references unknown column '{input_col}'",
                details=[{"field": "mapping", "message": f"unknown column: {input_col}"}],
            )
        if target not in TARGET_FIELDS:
            raise ValidationProblem(
                f"'{target}' is not a supported field",
                details=[{"field": "mapping", "message": f"unsupported target: {target}"}],
            )
        if target in mapping.values():
            raise ValidationProblem(
                f"two columns are mapped to '{target}'",
                details=[{"field": "mapping", "message": f"duplicate target: {target}"}],
            )
        mapping[input_col] = target

    missing = [field for field in REQUIRED_FIELDS if field not in mapping.values()]
    if missing:
        raise ValidationProblem(
            "required fields are not mapped: " + ", ".join(missing),
            details=[{"field": "mapping", "message": f"missing: {field}"} for field in missing],
        )
    return mapping


def _validate_rows(
    frame: pd.DataFrame, mapping: dict[str, str]
) -> tuple[list[dict], list[ImportRowError]]:
    """Return (accepted payloads carrying their file row number, row errors)."""
    renamed = frame.rename(columns=mapping)[list(mapping.values())]
    accepted: list[dict] = []
    errors: list[ImportRowError] = []

    timestamps = pd.to_datetime(renamed["timestamp"], errors="coerce", utc=True, format="mixed")
    numeric: dict[str, pd.Series] = {}
    for field in _FIELD_BOUNDS:
        if field in renamed.columns:
            numeric[field] = pd.to_numeric(renamed[field], errors="coerce")

    seen_timestamps: set[datetime] = set()
    for position in range(len(renamed)):
        row_number = position + 2  # header is line 1
        ts = timestamps.iloc[position]
        if pd.isna(ts):
            errors.append(
                ImportRowError(
                    row=row_number,
                    field="timestamp",
                    message="unparseable timestamp (expected ISO 8601; naive values are UTC)",
                )
            )
            continue
        timestamp = ts.to_pydatetime()
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC)
        if timestamp in seen_timestamps:
            errors.append(
                ImportRowError(
                    row=row_number,
                    field="timestamp",
                    message=f"duplicate timestamp {timestamp.isoformat()} within the file",
                )
            )
            continue
        seen_timestamps.add(timestamp)

        values: dict[str, float | None] = {}
        row_failed = False
        for field, (low, high) in _FIELD_BOUNDS.items():
            if field not in numeric:
                continue
            value = numeric[field].iloc[position]
            if pd.isna(value):
                original = renamed.iloc[position][field]
                if field == "pressure" and pd.isna(original):
                    values["pressure"] = None  # blank optional cell is allowed
                    continue
                errors.append(ImportRowError(row=row_number, field=field, message="not a number"))
                row_failed = True
                break
            if not low <= float(value) <= high:
                errors.append(
                    ImportRowError(
                        row=row_number,
                        field=field,
                        message=f"value {value} outside allowed range {low:g}..{high:g}",
                    )
                )
                row_failed = True
                break
            values[field] = float(value)
        if row_failed:
            continue

        accepted.append({"row": row_number, "timestamp": timestamp, **values})
    return accepted, errors


def _cap_errors(errors: list[ImportRowError]) -> tuple[list[ImportRowError], bool]:
    if len(errors) <= MAX_REPORTED_ERRORS:
        return errors, False
    return errors[:MAX_REPORTED_ERRORS], True


def _existing_timestamps(db: Session, machine_id: int, timestamps: list[datetime]) -> set[datetime]:
    found: set[datetime] = set()
    for start in range(0, len(timestamps), _DUPLICATE_CHUNK):
        chunk = timestamps[start : start + _DUPLICATE_CHUNK]
        rows = db.scalars(
            select(SensorReading.timestamp).where(
                SensorReading.machine_id == machine_id,
                SensorReading.timestamp.in_(chunk),
            )
        ).all()
        found.update(rows)
    return found


def validate_or_import(
    db: Session,
    *,
    raw: bytes,
    filename: str,
    machine_id: int,
    mapping_json: str,
    dry_run: bool,
) -> ImportReport:
    machine = db.get(Machine, machine_id)
    if machine is None:
        raise NotFoundError("Machine", machine_id)

    frame = _read_frame(raw, filename)
    headers = [str(col) for col in frame.columns]
    mapping = _parse_mapping(mapping_json, headers)

    accepted, errors = _validate_rows(frame, mapping)

    # Duplicates against persisted history are row-rejected, not 409s: the
    # report must show which rows did not land.
    existing = _existing_timestamps(db, machine_id, [row["timestamp"] for row in accepted])
    if existing:
        kept: list[dict] = []
        for row in accepted:
            if row["timestamp"] in existing:
                errors.append(
                    ImportRowError(
                        row=row["row"],
                        field="timestamp",
                        message=(
                            f"already exists for this machine at {row['timestamp'].isoformat()}"
                        ),
                    )
                )
            else:
                kept.append(row)
        accepted = kept

    total = len(frame)
    rejected = len(errors)
    accepted_count = len(accepted)
    capped, truncated = _cap_errors(errors)

    if dry_run:
        return ImportReport(
            dry_run=True,
            filename=filename,
            total_rows=total,
            accepted_rows=accepted_count,
            rejected_rows=rejected,
            errors=capped,
            errors_truncated=truncated,
        )

    job = DataImportJob(
        filename=filename,
        file_size_bytes=len(raw),
        machine_id=machine_id,
        status=ImportStatus.processing,
        total_rows=total,
        accepted_rows=accepted_count,
        rejected_rows=rejected,
        column_mapping=mapping,
        errors=[error.model_dump() for error in capped],
    )
    db.add(job)
    try:
        db.flush()  # allocate job id for readings' import_job_id FK
        readings = [
            SensorReading(
                machine_id=machine_id,
                timestamp=row["timestamp"],
                vibration_rms=Decimal(str(row["vibration_rms"])),
                temperature=Decimal(str(row["temperature"])),
                rpm=Decimal(str(row["rpm"])),
                load_pct=Decimal(str(row["load_pct"])),
                pressure=(
                    Decimal(str(row["pressure"])) if row.get("pressure") is not None else None
                ),
                source=ReadingSource.imported,
                import_job_id=job.id,
                quality_metadata={"import_errors_truncated": True} if truncated else None,
            )
            for row in accepted
        ]
        db.add_all(readings)
        db.flush()
        # Detection over the imported window in the SAME transaction.
        for reading in readings:
            detection_service.process_reading(db, reading)
        job.status = ImportStatus.completed if accepted_count > 0 else ImportStatus.failed
        job.completed_at = datetime.now(UTC)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return ImportReport(
        dry_run=False,
        filename=filename,
        total_rows=total,
        accepted_rows=accepted_count,
        rejected_rows=rejected,
        errors=capped,
        errors_truncated=truncated,
        job_id=job.id,
    )


def list_jobs(
    db: Session, *, offset: int, limit: int
) -> tuple[list[tuple[DataImportJob, Machine | None]], int]:
    total = db.scalar(select(func.count()).select_from(DataImportJob)) or 0
    rows = db.execute(
        select(DataImportJob, Machine)
        .join(Machine, DataImportJob.machine_id == Machine.id, isouter=True)
        .order_by(DataImportJob.created_at.desc(), DataImportJob.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return [(job, machine) for job, machine in rows], int(total)


def get_job(db: Session, job_id: int) -> tuple[DataImportJob, Machine | None]:
    job = db.get(DataImportJob, job_id)
    if job is None:
        raise NotFoundError("Import job", job_id)
    machine = db.get(Machine, job.machine_id) if job.machine_id else None
    return job, machine
