"""Sensor reading schemas and query filters."""

import enum
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReadingSource(enum.StrEnum):
    simulated = "simulated"
    imported = "imported"
    live = "live"  # direct API ingestion (simulation step, manual entry)


class ReadingCreate(BaseModel):
    """New sensor measurement submitted through the ingestion API."""

    machine_id: int = Field(ge=1)
    timestamp: datetime | None = Field(
        default=None,
        description="ISO 8601 (tz-aware preferred; naive is interpreted as UTC). Defaults to now.",
    )
    vibration_rms: float = Field(ge=0, le=500, description="mm/s RMS")
    temperature: float = Field(ge=-100, le=1500, description="°C")
    rpm: float = Field(ge=0, le=1_000_000, description="rev/min")
    load_pct: float = Field(ge=0, le=100, description="%")
    pressure: float | None = Field(default=None, ge=0, le=1000, description="bar (optional sensor)")
    source: ReadingSource = ReadingSource.live

    @field_validator("timestamp", mode="after")
    @classmethod
    def _assume_utc(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value


class ReadingRead(BaseModel):
    """A single persisted sensor measurement.

    Units: vibration_rms mm/s (RMS), temperature degC, rpm rev/min,
    load_pct %, pressure bar.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    machine_id: int
    timestamp: datetime
    vibration_rms: float
    temperature: float
    rpm: float
    load_pct: float
    pressure: float | None
    source: ReadingSource
    import_job_id: int | None

    @field_validator("vibration_rms", "temperature", "rpm", "load_pct", "pressure", mode="before")
    @classmethod
    def _numeric_to_float(cls, value: object) -> object:
        """Decimal (Numeric column) -> float for API JSON numbers."""
        return float(value) if value is not None else None

    @field_validator("source", mode="before")
    @classmethod
    def _enum_value(cls, value: object) -> object:
        return value.value if isinstance(value, enum.Enum) else value


class ReadingIngestResponse(BaseModel):
    """Acknowledgement of an accepted reading plus detection side effects."""

    reading: ReadingRead
    affected_anomaly_ids: list[int] = Field(
        default_factory=list,
        description="Anomaly events created or extended while processing this reading",
    )
