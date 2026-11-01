"""Maintenance work-order endpoints (list, create, detail, update)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.api.v1.pagination import PageDep, build_page, offset_for
from app.db.session import get_db
from app.repositories import maintenance as maintenance_repo
from app.schemas.common import Page
from app.schemas.maintenance import (
    MaintenancePriority,
    MaintenanceType,
    WorkOrderCreate,
    WorkOrderRead,
    WorkOrderStatus,
    WorkOrderUpdate,
)
from app.services import maintenance as maintenance_service

router = APIRouter(prefix="/maintenance", tags=["maintenance"])

DbDep = Annotated[Session, Depends(get_db)]


@router.get("", response_model=Page[WorkOrderRead], summary="List work orders")
def list_work_orders(
    db: DbDep,
    pagination: PageDep,
    machine_id: int | None = Query(default=None, ge=1),
    work_order_status: WorkOrderStatus | None = Query(default=None, alias="status"),
    priority: MaintenancePriority | None = None,
    maintenance_type: MaintenanceType | None = Query(default=None, alias="type"),
    overdue: bool = Query(
        default=False, description="Past scheduled date and not completed/cancelled"
    ),
    upcoming: bool = Query(default=False, description="Scheduled within the next 7 days"),
    sort: str = Query(
        default="scheduled_date",
        pattern="^(scheduled_date|priority|status|created_at|title)$",
    ),
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
) -> Page[WorkOrderRead]:
    page, page_size = pagination
    items, total = maintenance_repo.list_work_orders(
        db,
        machine_id=machine_id,
        status=work_order_status.value if work_order_status else None,
        priority=priority.value if priority else None,
        maintenance_type=maintenance_type.value if maintenance_type else None,
        overdue=overdue,
        upcoming=upcoming,
        sort=sort,
        descending=order == "desc",
        offset=offset_for(page, page_size),
        limit=page_size,
    )
    return build_page(
        [WorkOrderRead.model_validate(order) for order in items],
        total,
        page,
        page_size,
        Page[WorkOrderRead],
    )


@router.post(
    "",
    response_model=WorkOrderRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a work order",
)
def create_work_order(payload: WorkOrderCreate, db: DbDep) -> WorkOrderRead:
    order = maintenance_service.create_work_order(db, payload)
    return WorkOrderRead.model_validate(order)


@router.get("/{work_order_id}", response_model=WorkOrderRead, summary="Work-order detail")
def get_work_order(
    work_order_id: Annotated[int, Path(ge=1)],
    db: DbDep,
) -> WorkOrderRead:
    order = maintenance_service.get_or_404(db, work_order_id)
    return WorkOrderRead.model_validate(order)


@router.patch("/{work_order_id}", response_model=WorkOrderRead, summary="Update a work order")
def update_work_order(
    work_order_id: Annotated[int, Path(ge=1)],
    payload: WorkOrderUpdate,
    db: DbDep,
) -> WorkOrderRead:
    order = maintenance_service.get_or_404(db, work_order_id)
    updated = maintenance_service.update_work_order(db, order, payload)
    return WorkOrderRead.model_validate(updated)
