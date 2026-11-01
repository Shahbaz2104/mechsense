"""Machine (asset) schemas."""

import enum
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Metrics that support configurable thresholds (pressure is optional per machine).
THRESHOLD_METRICS = ("vibration_rms", "temperature", "rpm", "load_pct", "pressure")


class EquipmentType(enum.StrEnum):
    pump = "pump"
    motor = "motor"
    fan = "fan"
    compressor = "compressor"
    bearing = "bearing"
    gearbox = "gearbox"
    conveyor = "conveyor"
    other = "other"


class MachineStatus(enum.StrEnum):
    active = "active"
    inactive = "inactive"


class HealthStatus(enum.StrEnum):
    """Derived machine health (never stored — computed on read)."""

    healthy = "healthy"
    warning = "warning"
    critical = "critical"
    inactive = "inactive"
    no_data = "no_data"


class MetricThresholds(BaseModel):
    """Warning/critical thresholds for a single sensor metric."""

    model_config = ConfigDict(extra="forbid")

    warning: float | None = Field(default=None, ge=0)
    critical: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _check_order(self) -> "MetricThresholds":
        if self.warning is not None and self.critical is not None and self.critical <= self.warning:
            raise ValueError("critical threshold must be greater than warning threshold")
        return self


class MachineThresholds(BaseModel):
    """Per-machine threshold configuration keyed by metric name."""

    model_config = ConfigDict(extra="forbid")

    vibration_rms: MetricThresholds | None = None
    temperature: MetricThresholds | None = None
    rpm: MetricThresholds | None = None
    load_pct: MetricThresholds | None = None
    pressure: MetricThresholds | None = None

    def as_storage(self) -> dict:
        """Compact dict for JSONB storage (drops unset metrics)."""
        data = self.model_dump(exclude_none=True)
        return data


class MachineCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    identifier: str = Field(min_length=2, max_length=32, pattern=r"^[A-Za-z0-9][A-Za-z0-9\-_]*$")
    name: str = Field(min_length=1, max_length=120)
    equipment_type: EquipmentType
    location: str | None = Field(default=None, max_length=120)
    manufacturer: str | None = Field(default=None, max_length=120)
    model: str | None = Field(default=None, max_length=120)
    installation_date: date | None = None
    description: str | None = Field(default=None, max_length=2000)
    thresholds: MachineThresholds = Field(default_factory=MachineThresholds)

    @field_validator("identifier")
    @classmethod
    def _identifier_case(cls, value: str) -> str:
        return value.upper()


class MachineUpdate(BaseModel):
    """Partial update: every field optional, absent fields keep current values."""

    model_config = ConfigDict(str_strip_whitespace=True)

    identifier: str | None = Field(
        default=None, min_length=2, max_length=32, pattern=r"^[A-Za-z0-9][A-Za-z0-9\-_]*$"
    )
    name: str | None = Field(default=None, min_length=1, max_length=120)
    equipment_type: EquipmentType | None = None
    location: str | None = Field(default=None, max_length=120)
    manufacturer: str | None = Field(default=None, max_length=120)
    model: str | None = Field(default=None, max_length=120)
    installation_date: date | None = None
    status: MachineStatus | None = None
    description: str | None = Field(default=None, max_length=2000)
    thresholds: MachineThresholds | None = None

    @field_validator("identifier")
    @classmethod
    def _identifier_case(cls, value: str | None) -> str | None:
        return value.upper() if value is not None else value


class MachineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    identifier: str
    name: str
    equipment_type: str
    location: str | None
    manufacturer: str | None
    model: str | None
    installation_date: date | None
    status: MachineStatus
    description: str | None
    thresholds: dict
    created_at: datetime
    updated_at: datetime

    @field_validator("status", mode="before")
    @classmethod
    def _status_value(cls, value: object) -> object:
        return value.value if isinstance(value, enum.Enum) else value


class AnomalyBrief(BaseModel):
    id: int
    metric: str
    severity: str
    detected_at: datetime
    status: str


class MachineSummary(BaseModel):
    """Machine list row enriched with derived health context (dashboard/list)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    identifier: str
    name: str
    equipment_type: str
    status: MachineStatus
    health_status: str  # healthy | warning | critical | inactive | no_data
    latest_reading_at: datetime | None
    vibration_rms: float | None
    temperature: float | None
    latest_anomaly: AnomalyBrief | None = None
    open_anomaly_count: int = 0

    @field_validator("status", mode="before")
    @classmethod
    def _status_value(cls, value: object) -> object:
        return value.value if isinstance(value, enum.Enum) else value


def machine_thresholds_from_storage(data: dict) -> MachineThresholds:
    """Parse the JSONB thresholds column into a validated schema (tolerant of {})."""
    known = {k: v for k, v in (data or {}).items() if k in THRESHOLD_METRICS}
    return MachineThresholds.model_validate(known)
