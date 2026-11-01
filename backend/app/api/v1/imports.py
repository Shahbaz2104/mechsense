"""CSV import endpoints: preview, dry-run validation, atomic import, history."""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi import Path as PathParam
from sqlalchemy.orm import Session

from app.api.v1.pagination import PageDep, build_page, offset_for
from app.db.session import get_db
from app.schemas.common import Page
from app.schemas.data_import import (
    ImportJobDetail,
    ImportJobRead,
    ImportJobRef,
    ImportPreviewResponse,
    ImportReport,
    ImportRowError,
)
from app.services import imports as import_service

router = APIRouter(prefix="/imports", tags=["imports"])

DbDep = Annotated[Session, Depends(get_db)]
JobId = Annotated[int, PathParam(ge=1)]


def _safe_filename(filename: str | None) -> str:
    name = Path(filename or "upload.csv").name.strip() or "upload.csv"
    return name[:255]


def _job_ref(machine) -> ImportJobRef | None:
    if machine is None:
        return None
    return ImportJobRef(id=machine.id, identifier=machine.identifier, name=machine.name)


def _job_read(job, machine) -> ImportJobRead:
    return ImportJobRead(
        id=job.id,
        filename=job.filename,
        machine=_job_ref(machine),
        status=job.status,
        total_rows=job.total_rows,
        accepted_rows=job.accepted_rows,
        rejected_rows=job.rejected_rows,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )


@router.post(
    "/preview",
    response_model=ImportPreviewResponse,
    summary="Parse an uploaded CSV and suggest a column mapping",
)
async def preview_import(
    file: Annotated[UploadFile, File(description="CSV file")],
) -> ImportPreviewResponse:
    raw = await file.read()
    return import_service.preview_upload(raw, _safe_filename(file.filename))


@router.post(
    "/csv",
    response_model=ImportReport,
    summary="Validate (dry_run=true) or import a mapped CSV",
)
async def import_csv(
    db: DbDep,
    file: Annotated[UploadFile, File(description="CSV file")],
    machine_id: Annotated[int, Form(ge=1)],
    mapping: Annotated[
        str, Form(description='JSON object: input column -> field, e.g. {"ts": "timestamp"}')
    ],
    dry_run: Annotated[bool, Query(description="Validate only; write nothing")] = False,
) -> ImportReport:
    raw = await file.read()
    return import_service.validate_or_import(
        db,
        raw=raw,
        filename=_safe_filename(file.filename),
        machine_id=machine_id,
        mapping_json=mapping,
        dry_run=dry_run,
    )


@router.get("", response_model=Page[ImportJobRead], summary="List import jobs (history)")
def list_imports(
    db: DbDep,
    pagination: PageDep,
) -> Page[ImportJobRead]:
    page, page_size = pagination
    rows, total = import_service.list_jobs(db, offset=offset_for(page, page_size), limit=page_size)
    items = [_job_read(job, machine) for job, machine in rows]
    return build_page(items, total, page, page_size, Page[ImportJobRead])


@router.get("/{job_id}", response_model=ImportJobDetail, summary="Import job detail")
def import_job_detail(db: DbDep, job_id: JobId) -> ImportJobDetail:
    job, machine = import_service.get_job(db, job_id)
    stored = [ImportRowError(**entry) for entry in (job.errors or [])]
    base = _job_read(job, machine)
    return ImportJobDetail(
        **base.model_dump(),
        column_mapping=job.column_mapping,
        errors=stored,
        errors_truncated=job.rejected_rows > len(stored),
    )
