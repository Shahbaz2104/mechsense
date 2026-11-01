"""Trend analytics schemas: time-bucketed metric series for charts."""

import enum
from datetime import datetime

from pydantic import BaseModel, Field


class TrendMetric(enum.StrEnum):
    vibration_rms = "vibration_rms"
    temperature = "temperature"
    rpm = "rpm"
    load_pct = "load_pct"
    pressure = "pressure"


METRIC_UNITS: dict[str, str] = {
    "vibration_rms": "mm/s",
    "temperature": "°C",
    "rpm": "rpm",
    "load_pct": "%",
    "pressure": "bar",
}


class TrendPoint(BaseModel):
    bucket_start: datetime
    avg: float | None = None
    min: float
    max: float
    count: int = Field(ge=0)


class TrendSeries(BaseModel):
    machine_id: int
    machine_identifier: str
    machine_name: str
    points: list[TrendPoint]


class TrendSummary(BaseModel):
    reading_count: int = 0
    avg: float | None = None
    min: float | None = None
    max: float | None = None
    p95: float | None = None


class TrendsResponse(BaseModel):
    metric: TrendMetric
    unit: str
    start: datetime
    end: datetime
    machine_id: int | None = None
    buckets: int
    bucket_seconds: float
    summary: TrendSummary
    series: list[TrendSeries]
