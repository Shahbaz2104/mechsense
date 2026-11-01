"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import (
    analytics,
    anomalies,
    dashboard,
    imports,
    machines,
    maintenance,
    readings,
    simulation,
)

api_router = APIRouter()

api_router.include_router(machines.router)
api_router.include_router(readings.router)
api_router.include_router(anomalies.router)
api_router.include_router(dashboard.router)
api_router.include_router(maintenance.router)
api_router.include_router(imports.router)
api_router.include_router(simulation.step_router)
api_router.include_router(simulation.demo_router)
api_router.include_router(analytics.trends_router)
api_router.include_router(analytics.config_router)
