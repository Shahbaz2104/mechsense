"""Simulation schemas: interactive step + batch demo generation."""

from pydantic import BaseModel, Field


class SimulationStepRequest(BaseModel):
    machine_id: int = Field(ge=1)


class DemoGenerateRequest(BaseModel):
    machine_id: int | None = Field(
        default=None,
        ge=1,
        description="Target one machine; omitted = every active machine",
    )
    count: int = Field(
        default=12,
        ge=1,
        description="New readings appended per machine (batch limit is configurable)",
    )


class DemoGenerateResponse(BaseModel):
    machines_processed: int
    readings_created: int
    anomaly_events_created: int
    skipped_inactive: list[str] = Field(
        default_factory=list, description="Identifiers of inactive machines not simulated"
    )
