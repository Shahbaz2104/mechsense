"""Fleet trend analytics: SQL-side time buckets for chart endpoints."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, ValidationProblem
from app.models import Machine, SensorReading
from app.schemas.analytics import (
    METRIC_UNITS,
    TrendMetric,
    TrendPoint,
    TrendSeries,
    TrendsResponse,
    TrendSummary,
)

DEFAULT_WINDOW = timedelta(hours=24)


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _float(value) -> float | None:
    return None if value is None else float(value)


def get_trends(
    db: Session,
    *,
    metric: TrendMetric,
    machine_id: int | None,
    start: datetime | None,
    end: datetime | None,
    buckets: int,
) -> TrendsResponse:
    end_utc = _as_utc(end) or datetime.now(UTC)
    start_utc = _as_utc(start) or (end_utc - DEFAULT_WINDOW)
    if start_utc >= end_utc:
        raise ValidationProblem("start must be before end")
    if machine_id is not None and db.get(Machine, machine_id) is None:
        raise NotFoundError("Machine", machine_id)

    column = getattr(SensorReading, metric.value)
    span = (end_utc - start_utc).total_seconds()
    bucket_seconds = span / buckets
    bucket_expr = func.floor(
        func.extract("epoch", SensorReading.timestamp - start_utc) / bucket_seconds
    )

    filters = [
        SensorReading.timestamp >= start_utc,
        SensorReading.timestamp < end_utc,
        column.is_not(None),
    ]
    if machine_id is not None:
        filters.append(SensorReading.machine_id == machine_id)

    # Windowed aggregates in one grouped query (no N+1) plus one summary query.
    rows = db.execute(
        select(
            SensorReading.machine_id,
            bucket_expr.label("bucket"),
            func.avg(column).label("avg"),
            func.min(column).label("min"),
            func.max(column).label("max"),
            func.count(column).label("count"),
        )
        .where(*filters)
        .group_by(SensorReading.machine_id, bucket_expr)
        .order_by(SensorReading.machine_id, bucket_expr)
    ).all()

    summary_row = db.execute(
        select(
            func.count(column),
            func.avg(column),
            func.min(column),
            func.max(column),
            func.percentile_cont(0.95).within_group(column),
        ).where(*filters)
    ).one()

    machine_ids = {row.machine_id for row in rows}
    machines: dict[int, object] = {}
    if machine_ids:
        machines = {
            row.id: row
            for row in db.execute(
                select(Machine.id, Machine.identifier, Machine.name).where(
                    Machine.id.in_(machine_ids)
                )
            ).all()
        }

    series_map: dict[int, list[TrendPoint]] = {}
    for row in rows:
        index = min(int(row.bucket), buckets - 1)
        bucket_start = start_utc + timedelta(seconds=index * bucket_seconds)
        series_map.setdefault(row.machine_id, []).append(
            TrendPoint(
                bucket_start=bucket_start,
                avg=_float(row.avg),
                min=float(row.min),
                max=float(row.max),
                count=int(row.count),
            )
        )

    series = [
        TrendSeries(
            machine_id=machine_id_key,
            machine_identifier=machines[machine_id_key].identifier,
            machine_name=machines[machine_id_key].name,
            points=points,
        )
        for machine_id_key, points in sorted(series_map.items())
        if machine_id_key in machines
    ]

    return TrendsResponse(
        metric=metric,
        unit=METRIC_UNITS[metric.value],
        start=start_utc,
        end=end_utc,
        machine_id=machine_id,
        buckets=buckets,
        bucket_seconds=bucket_seconds,
        summary=TrendSummary(
            reading_count=int(summary_row[0]),
            avg=_float(summary_row[1]),
            min=_float(summary_row[2]),
            max=_float(summary_row[3]),
            p95=_float(summary_row[4]),
        ),
        series=series,
    )
