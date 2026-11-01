"""CSV import pipeline: preview, dry-run validation, atomic import, history."""

import json
from decimal import Decimal

from sqlalchemy import func, select

from app.models import AnomalyEvent, ReadingSource, SensorReading
from tests.conftest import error_body

CANONICAL = "timestamp,vibration_rms,temperature,rpm,load_pct,pressure\n"
SYNONYM = "ts,vibration,temp_c,speed,load,bar\n"
IDENTITY = json.dumps(
    {
        field: field
        for field in ("timestamp", "vibration_rms", "temperature", "rpm", "load_pct", "pressure")
    }
)
SYNONYM_MAPPING = json.dumps(
    {
        "ts": "timestamp",
        "vibration": "vibration_rms",
        "temp_c": "temperature",
        "speed": "rpm",
        "load": "load_pct",
        "bar": "pressure",
    }
)


def _post(client, raw, *, url, machine_id=None, mapping=None, params=None, name="data.csv"):
    data: dict[str, str] = {}
    if machine_id is not None:
        data["machine_id"] = str(machine_id)
    if mapping is not None:
        data["mapping"] = mapping if isinstance(mapping, str) else json.dumps(mapping)
    return client.post(
        url,
        files={"file": (name, raw, "text/csv")},
        data=data,
        params=params or {},
    )


def _preview(client, raw, name="data.csv"):
    return _post(client, raw, url="/api/v1/imports/preview", name=name)


def _csv(client, raw, machine_id, mapping=IDENTITY, dry_run=False, name="data.csv"):
    params = {"dry_run": "true"} if dry_run else {}
    return _post(
        client,
        raw,
        url="/api/v1/imports/csv",
        machine_id=machine_id,
        mapping=mapping,
        params=params,
        name=name,
    )


def test_preview_suggests_mapping_and_counts_rows(client):
    raw = (SYNONYM + "2026-01-15T10:00:00,5.0,70.0,1800,40,2.5\n").encode()
    body = _preview(client, raw, name="shift.csv").json()
    assert body["filename"] == "shift.csv"
    assert body["size_bytes"] == len(raw)
    assert body["row_count"] == 1
    assert body["headers"] == ["ts", "vibration", "temp_c", "speed", "load", "bar"]
    assert body["sample_rows"][0]["vibration"] == "5.0"
    assert body["mapping_candidates"]["timestamp"] == "ts"
    assert body["mapping_candidates"]["temperature"] == "temp_c"
    assert body["mapping_candidates"]["vibration_rms"] == "vibration"


def test_preview_rejects_empty_and_headers_only(client):
    assert _preview(client, b"").status_code == 422
    headers_only = _preview(client, CANONICAL.encode())
    assert headers_only.status_code == 422
    assert "no data rows" in error_body(headers_only.json())["message"]


def test_dry_run_reports_row_errors_without_writing(client, create_machine, db):
    machine = create_machine("IMP-1")
    raw = (
        CANONICAL
        + "2026-01-15T10:00:00Z,5.0,70.0,1800,40,2.5\n"  # line 2 ok
        + "not-a-time,5.0,70.0,1800,40,2.5\n"  # line 3 bad timestamp
        + "2026-01-15T10:01:00Z,abc,70.0,1800,40,2.5\n"  # line 4 bad number
        + "2026-01-15T10:02:00Z,5.0,70.0,1800,150,2.5\n"  # line 5 load out of range
        + "2026-01-15T10:03:00Z,5.0,70.0,1800,40,2.5\n"  # line 6 ok
        + "2026-01-15T10:03:00Z,5.0,70.0,1800,40,2.5\n"  # line 7 duplicate in file
    ).encode()

    report = _csv(client, raw, machine["id"], dry_run=True)
    assert report.status_code == 200, report.text
    body = report.json()
    assert body["dry_run"] is True
    assert body["total_rows"] == 6
    assert body["accepted_rows"] == 2
    assert body["rejected_rows"] == 4
    assert body["job_id"] is None
    assert {error["row"] for error in body["errors"]} == {3, 4, 5, 7}
    by_row = {error["row"]: error for error in body["errors"]}
    assert by_row[3]["field"] == "timestamp"
    assert by_row[4]["field"] == "vibration_rms"
    assert by_row[5]["field"] == "load_pct"
    assert "duplicate timestamp" in by_row[7]["message"]

    # Nothing written: no readings, no jobs.
    assert db.scalar(select(func.count()).select_from(SensorReading)) == 0
    assert client.get("/api/v1/imports").json()["total"] == 0


def test_import_persists_runs_detection_and_links_job(client, create_machine, db):
    machine = create_machine(
        "IMP-2", thresholds={"vibration_rms": {"warning": 4.5, "critical": 7.1}}
    )
    raw = (
        CANONICAL
        + "2026-01-15T10:00:00,5.0,70.0,1800,40,\n"  # naive ts + blank pressure
        + "2026-01-15T10:01:00Z,9.4,80.0,1800,55,3.1\n"  # critical vibration
    ).encode()

    report = _csv(client, raw, machine["id"])
    assert report.status_code == 200, report.text
    body = report.json()
    assert body["dry_run"] is False
    assert body["accepted_rows"] == 2
    assert body["rejected_rows"] == 0
    assert body["job_id"] is not None

    # Job history + detail.
    history = client.get("/api/v1/imports").json()
    assert history["total"] == 1
    job = history["items"][0]
    assert job["status"] == "completed"
    assert job["machine"]["identifier"] == "IMP-2"
    detail = client.get(f"/api/v1/imports/{job['id']}").json()
    assert detail["column_mapping"]["timestamp"] == "timestamp"
    assert detail["errors"] == []
    assert detail["errors_truncated"] is False

    # Readings persisted, source/job linked, naive timestamp interpreted as UTC.
    readings = db.scalars(
        select(SensorReading)
        .where(SensorReading.machine_id == machine["id"])
        .order_by(SensorReading.timestamp)
    ).all()
    assert len(readings) == 2
    assert readings[0].timestamp.isoformat() == "2026-01-15T10:00:00+00:00"
    assert readings[0].pressure is None
    assert readings[0].source == ReadingSource.imported
    assert readings[0].import_job_id == job["id"]
    assert readings[1].vibration_rms == Decimal("9.4")

    # Detection ran inside the import transaction.
    events = client.get("/api/v1/anomalies", params={"machine_id": machine["id"]}).json()
    assert events["total"] == 1
    assert events["items"][0]["metric"] == "vibration_rms"
    assert events["items"][0]["severity"] == "critical"
    assert db.scalar(select(func.count()).select_from(AnomalyEvent)) == 1


def test_reimport_rejects_persisted_duplicates(client, create_machine, db):
    machine = create_machine("IMP-3")
    raw = (
        CANONICAL
        + "2026-01-15T10:00:00Z,5.0,70.0,1800,40,2.5\n"
        + "2026-01-15T10:01:00Z,5.0,70.0,1800,40,2.5\n"
    ).encode()

    first = _csv(client, raw, machine["id"]).json()
    assert first["accepted_rows"] == 2

    second = _csv(client, raw, machine["id"])
    assert second.status_code == 200
    body = second.json()
    assert body["accepted_rows"] == 0
    assert body["rejected_rows"] == 2
    assert all("already exists" in error["message"] for error in body["errors"])
    assert {error["row"] for error in body["errors"]} == {2, 3}

    detail = client.get(f"/api/v1/imports/{body['job_id']}").json()
    assert detail["status"] == "failed"

    count = db.scalar(select(func.count()).select_from(SensorReading))
    assert count == 2  # atomic: nothing partial landed


def test_mapping_validation_errors(client, create_machine):
    machine = create_machine("IMP-4")
    raw = (CANONICAL + "2026-01-15T10:00:00Z,5.0,70.0,1800,40,2.5\n").encode()

    # missing required target
    incomplete = {k: v for k, v in json.loads(IDENTITY).items() if v != "load_pct"}
    response = _csv(client, raw, machine["id"], mapping=incomplete)
    assert response.status_code == 422
    assert "required fields" in error_body(response.json())["message"]

    # unknown input column
    unknown = dict(json.loads(IDENTITY))
    unknown["ghost"] = "pressure"
    response = _csv(client, raw, machine["id"], mapping=unknown)
    assert response.status_code == 422
    assert "ghost" in error_body(response.json())["message"]

    # unsupported target field
    unsupported = dict(json.loads(IDENTITY))
    unsupported["timestamp"] = "mass_flow"
    response = _csv(client, raw, machine["id"], mapping=unsupported)
    assert response.status_code == 422
    assert "mass_flow" in error_body(response.json())["message"]

    # two columns mapped to the same target
    duplicate = dict(json.loads(IDENTITY))
    duplicate["vibration_rms"] = "temperature"
    response = _csv(client, raw, machine["id"], mapping=duplicate)
    assert response.status_code == 422
    assert "mapped to" in error_body(response.json())["message"]


def test_import_missing_machine_is_404(client):
    raw = (CANONICAL + "2026-01-15T10:00:00Z,5.0,70.0,1800,40,2.5\n").encode()
    response = _csv(client, raw, 999999)
    assert response.status_code == 404


def test_size_and_row_limits(client, create_machine, monkeypatch):
    from types import SimpleNamespace

    machine = create_machine("IMP-5")
    monkeypatch.setattr(
        "app.services.imports.get_settings",
        lambda: SimpleNamespace(import_max_file_mb=1, import_max_rows=100_000),
    )
    big = b"x" * (1_100_000)
    response = _csv(client, big, machine["id"])
    assert response.status_code == 422
    assert "limit is 1 MB" in error_body(response.json())["message"]

    monkeypatch.setattr(
        "app.services.imports.get_settings",
        lambda: SimpleNamespace(import_max_file_mb=10, import_max_rows=2),
    )
    many = (
        CANONICAL
        + "2026-01-15T10:00:00Z,5.0,70.0,1800,40,2.5\n"
        + "2026-01-15T10:01:00Z,5.0,70.0,1800,40,2.5\n"
        + "2026-01-15T10:02:00Z,5.0,70.0,1800,40,2.5\n"
    ).encode()
    response = _csv(client, many, machine["id"])
    assert response.status_code == 422
    assert "limit is 2" in error_body(response.json())["message"]


def test_history_pagination_and_detail_404(client, create_machine):
    machine = create_machine("IMP-6")
    row = "2026-01-15T10:00:00Z,5.0,70.0,1800,40,2.5\n"
    for index in range(3):
        raw = (CANONICAL + row.replace("10:00", f"10:0{index}")).encode()
        assert _csv(client, raw, machine["id"], name=f"file{index}.csv").status_code == 200

    page = client.get("/api/v1/imports", params={"page": 2, "page_size": 2}).json()
    assert page["total"] == 3
    assert page["pages"] == 2
    assert len(page["items"]) == 1

    missing = client.get("/api/v1/imports/424242")
    assert missing.status_code == 404
    assert error_body(missing.json())["code"] == "not_found"
