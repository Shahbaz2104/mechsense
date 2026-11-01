"""Simulation endpoints: interactive step + batch demo generation."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.reading import ReadingIngestResponse
from app.schemas.simulation import DemoGenerateRequest, DemoGenerateResponse, SimulationStepRequest
from app.services import simulation as simulation_service

step_router = APIRouter(prefix="/simulation", tags=["simulation"])
demo_router = APIRouter(prefix="/demo", tags=["simulation"])

DbDep = Annotated[Session, Depends(get_db)]


@step_router.post(
    "/step",
    response_model=ReadingIngestResponse,
    summary="Generate the next reading for a machine (detect + notify)",
)
def simulation_step(db: DbDep, body: SimulationStepRequest) -> ReadingIngestResponse:
    return simulation_service.step(db, body.machine_id)


@demo_router.post(
    "/generate",
    response_model=DemoGenerateResponse,
    summary="Append a batch of deterministic demo readings",
)
def demo_generate(db: DbDep, body: DemoGenerateRequest) -> DemoGenerateResponse:
    return simulation_service.generate_demo(db, body)
