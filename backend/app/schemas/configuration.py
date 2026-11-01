"""Runtime configuration schemas exposed read-only to the Settings page."""

from pydantic import BaseModel, Field


class PaginationConfig(BaseModel):
    default_page_size: int
    max_page_size: int


class ImportsConfig(BaseModel):
    max_file_mb: int
    max_rows: int


class SimulationConfig(BaseModel):
    seed: int
    max_batch: int
    interval_minutes: int = Field(description="Cadence of generated readings")


class ConfigurationResponse(BaseModel):
    """Public runtime settings — never includes credentials or connection URLs."""

    app_name: str
    environment: str
    pagination: PaginationConfig
    imports: ImportsConfig
    simulation: SimulationConfig
