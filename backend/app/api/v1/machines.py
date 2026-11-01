"""Machine CRUD endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.v1.pagination import PageDep, build_page, offset_for
from app.db.session import get_db
from app.repositories import machines as machine_repo
from app.schemas.common import Page
from app.schemas.machine import (
    EquipmentType,
    HealthStatus,
    MachineCreate,
    MachineRead,
    MachineStatus,
    MachineSummary,
    MachineUpdate,
)
from app.services import machines as machine_service

router = APIRouter(prefix="/machines", tags=["machines"])

DbDep = Annotated[Session, Depends(get_db)]


@router.get("", response_model=Page[MachineSummary], summary="List machines")
def list_machines(
    db: DbDep,
    pagination: PageDep,
    search: str | None = Query(
        default=None, max_length=100, description="Substring match on name/identifier"
    ),
    equipment_type: EquipmentType | None = None,
    status_filter: MachineStatus | None = Query(default=None, alias="status"),
    health: HealthStatus | None = Query(
        default=None, description="Filter on derived health status"
    ),
    sort: str = Query(
        default="name",
        pattern="^(name|identifier|equipment_type|created_at|status)$",
    ),
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
) -> Page[MachineSummary]:
    page, page_size = pagination
    machines, total = machine_repo.list_machines(
        db,
        search=search,
        equipment_type=equipment_type.value if equipment_type else None,
        status=status_filter.value if status_filter else None,
        health=health.value if health else None,
        sort=sort,
        descending=order == "desc",
        offset=offset_for(page, page_size),
        limit=page_size,
    )
    summaries = machine_service.summarize_machines(db, machines)
    return build_page(summaries, total, page, page_size, Page[MachineSummary])


@router.post(
    "",
    response_model=MachineRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a machine",
)
def create_machine(payload: MachineCreate, db: DbDep) -> MachineRead:
    machine = machine_service.create_machine(db, payload)
    return MachineRead.model_validate(machine)


@router.get("/{machine_id}", response_model=MachineRead, summary="Machine detail")
def get_machine(machine_id: int, db: DbDep) -> MachineRead:
    machine = machine_service.get_machine_or_404(db, machine_id)
    return MachineRead.model_validate(machine)


@router.patch("/{machine_id}", response_model=MachineRead, summary="Update a machine")
def update_machine(machine_id: int, payload: MachineUpdate, db: DbDep) -> MachineRead:
    machine = machine_service.get_machine_or_404(db, machine_id)
    updated = machine_service.update_machine(db, machine, payload)
    return MachineRead.model_validate(updated)
