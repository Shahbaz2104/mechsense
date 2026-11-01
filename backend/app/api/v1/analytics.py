"""Trends and configuration endpoints."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.analytics import TrendMetric, TrendsResponse
from app.schemas.configuration import (
    ConfigurationResponse,
    ImportsConfig,
    PaginationConfig,
    SimulationConfig,
)
from app.services import analytics as analytics_service
from app.simulation.generator import READ_INTERVAL

trends_router = APIRouter(prefix="/analytics", tags=["analytics"])
config_router = APIRouter(prefix="/configuration", tags=["configuration"])

DbDep = Annotated[Session, Depends(get_db)]


@trends_router.get(
    "/trends",
    response_model=TrendsResponse,
    summary="Time-bucketed metric trends across machines",
)
def trends(
    db: DbDep,
    metric: Annotated[
        TrendMetric, Query(description="Sensor metric to aggregate")
    ] = TrendMetric.vibration_rms,
    machine_id: Annotated[int | None, Query(ge=1)] = None,
    start: Annotated[
        datetime | None, Query(description="Inclusive lower bound (ISO 8601; naive = UTC)")
    ] = None,
    end: Annotated[
        datetime | None, Query(description="Exclusive upper bound (ISO 8601; naive = UTC)")
    ] = None,
    buckets: Annotated[
        int, Query(ge=2, le=500, description="Number of equal-width time buckets")
    ] = 48,
) -> TrendsResponse:
    return analytics_service.get_trends(
        db, metric=metric, machine_id=machine_id, start=start, end=end, buckets=buckets
    )


@config_router.get(
    "",
    response_model=ConfigurationResponse,
    summary="Read-only runtime configuration for the Settings page",
)
def configuration() -> ConfigurationResponse:
    settings = get_settings()
    return ConfigurationResponse(
        app_name=settings.app_name,
        environment=settings.environment,
        pagination=PaginationConfig(
            default_page_size=settings.default_page_size,
            max_page_size=settings.max_page_size,
        ),
        imports=ImportsConfig(
            max_file_mb=settings.import_max_file_mb,
            max_rows=settings.import_max_rows,
        ),
        simulation=SimulationConfig(
            seed=settings.simulation_seed,
            max_batch=settings.simulation_max_batch,
            interval_minutes=int(READ_INTERVAL.total_seconds() // 60),
        ),
    )
