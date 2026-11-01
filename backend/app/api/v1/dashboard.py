"""Dashboard summary endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.dashboard import ActivityResponse, DashboardResponse
from app.services import dashboard as dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

DbDep = Annotated[Session, Depends(get_db)]


@router.get(
    "/summary",
    response_model=DashboardResponse,
    summary="Aggregated overview for the selected period",
)
def dashboard_summary(
    db: DbDep,
    period: str = Query(
        default="7d",
        pattern="^(1h|6h|24h|7d|30d)$",
        description="Window used for anomaly counts and previous-period comparison",
    ),
) -> DashboardResponse:
    return dashboard_service.build_dashboard(db, period=period)


@router.get(
    "/activity",
    response_model=ActivityResponse,
    summary="Latest operational events (imports, anomalies, acks, work orders)",
)
def dashboard_activity(
    db: DbDep,
    limit: int = Query(default=10, ge=1, le=50),
) -> ActivityResponse:
    return dashboard_service.build_activity(db, limit=limit)
