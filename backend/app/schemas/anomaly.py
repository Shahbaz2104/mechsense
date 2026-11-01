"""Anomaly event schemas (list, detail, acknowledge/resolve actions)."""

import enum
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


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


class AnomalyMachineRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    identifier: str
    name: str


class AnomalyReadingRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    vibration_rms: float
    temperature: float
    rpm: float
    load_pct: float
    pressure: float | None


class AnomalyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    machine: AnomalyMachineRef
    reading_id: int
    reading: AnomalyReadingRef | None = None
    metric: str
    observed_value: float
    threshold_value: float | None
    severity: AnomalySeverity
    method: AnomalyMethod
    status: AnomalyStatus
    detected_at: datetime
    last_seen_at: datetime
    acknowledged_at: datetime | None
    resolved_at: datetime | None
    explanation: str
    notes: str | None

    @field_validator("observed_value", "threshold_value", mode="before")
    @classmethod
    def _numeric_to_float(cls, value: object) -> object:
        return float(value) if value is not None else None

    @field_validator("severity", "method", "status", mode="before")
    @classmethod
    def _enum_value(cls, value: object) -> object:
        return value.value if isinstance(value, enum.Enum) else value


class AnomalyActionRequest(BaseModel):
    """Optional investigation note for acknowledge/resolve actions."""

    notes: str | None = Field(default=None, max_length=4000)


class AnomalyCounts(BaseModel):
    """Counts by status/severity used by filters and dashboard chips."""

    open: int = 0
    acknowledged: int = 0
    resolved: int = 0
    warning: int = 0
    critical: int = 0
