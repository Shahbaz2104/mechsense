"""Simulation endpoints: interactive step + batch demo generation."""

from sqlalchemy import func, select

from app.models import ReadingSource, SensorReading
from tests.conftest import error_body

# F-301 fallback profile runs healthy at ~3.1 mm/s; these thresholds fire
# deterministically on every generated reading.
CRITICAL_VIBRATION = {"vibration_rms": {"warning": 0.1, "critical": 0.5}}


def _count(db) -> int:
    return db.scalar(select(func.count()).select_from(SensorReading)) or 0


def stamp_is_utc(stamp: str) -> bool:
    return stamp.endswith("Z") or stamp.endswith("+00:00")


def test_step_appends_reading_and_detects(client, create_machine, db):
    machine = create_machine("SIM-1", thresholds=CRITICAL_VIBRATION)

    response = client.post("/api/v1/simulation/step", json={"machine_id": machine["id"]})
    assert response.status_code == 200, response.text
    body = response.json()
    reading = body["reading"]
    assert reading["machine_id"] == machine["id"]
    assert reading["source"] == ReadingSource.simulated
    assert reading["vibration_rms"] >= 2.0  # healthy fallback profile base ~3.1
    assert body["affected_anomaly_ids"], "critical threshold must create an event"
    assert stamp_is_utc(reading["timestamp"])
    assert _count(db) == 1

    # A second step continues the simulated 5-minute grid and extends the
    # still-open event (duplicate suppression merges consecutive violations).
    again = client.post("/api/v1/simulation/step", json={"machine_id": machine["id"]})
    assert again.status_code == 200
    second = again.json()["reading"]
    assert second["timestamp"] > reading["timestamp"]
    assert again.json()["affected_anomaly_ids"], "extend must reference the open event"
    assert _count(db) == 2

    events = client.get("/api/v1/anomalies", params={"machine_id": machine["id"]}).json()
    assert events["total"] == 1  # merged into one still-open critical event


def test_step_on_empty_machine_starts_at_current_time(client, create_machine, db):
    from datetime import UTC, datetime

    machine = create_machine("SIM-2")
    before = datetime.now(UTC)
    response = client.post("/api/v1/simulation/step", json={"machine_id": machine["id"]})
    assert response.status_code == 200
    stamp = response.json()["reading"]["timestamp"]
    parsed = datetime.fromisoformat(stamp)
    assert parsed >= before


def test_step_missing_and_inactive_machine(client, create_machine):
    assert client.post("/api/v1/simulation/step", json={"machine_id": 999999}).status_code == 404

    machine = create_machine("SIM-3")
    assert (
        client.patch(f"/api/v1/machines/{machine['id']}", json={"status": "inactive"}).status_code
        == 200
    )
    response = client.post("/api/v1/simulation/step", json={"machine_id": machine["id"]})
    assert response.status_code == 409
    assert error_body(response.json())["code"] == "invalid_state"


def test_demo_generate_fleet_batch(client, create_machine, db):
    flagged = create_machine("SIM-4", thresholds=CRITICAL_VIBRATION)
    quiet = create_machine("SIM-5")

    response = client.post("/api/v1/demo/generate", json={"count": 3})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["machines_processed"] == 2
    assert body["readings_created"] == 6
    assert body["anomaly_events_created"] >= 3  # flagged machine fires per row
    assert body["skipped_inactive"] == []

    for machine_id in (flagged["id"], quiet["id"]):
        rows = db.scalars(
            select(SensorReading)
            .where(SensorReading.machine_id == machine_id)
            .order_by(SensorReading.timestamp)
        ).all()
        assert len(rows) == 3
        assert all(row.source == ReadingSource.simulated for row in rows)
        # strictly increasing 5-minute spacing (empty machine anchors to "now")
        deltas = [
            (rows[i + 1].timestamp - rows[i].timestamp).total_seconds()
            for i in range(len(rows) - 1)
        ]
        assert deltas == [300.0, 300.0]


def test_demo_generate_single_machine_and_inactive_skipped(client, create_machine, db):
    target = create_machine("SIM-6")
    create_machine("SIM-7")
    inactive = create_machine("SIM-8")
    assert (
        client.patch(f"/api/v1/machines/{inactive['id']}", json={"status": "inactive"}).status_code
        == 200
    )

    body = client.post(
        "/api/v1/demo/generate", json={"machine_id": target["id"], "count": 2}
    ).json()
    assert body["machines_processed"] == 1
    assert body["readings_created"] == 2
    assert body["skipped_inactive"] == []
    assert _count(db) == 2

    # Fleet run skips inactive machines and reports them.
    fleet = client.post("/api/v1/demo/generate", json={"count": 1}).json()
    assert fleet["machines_processed"] == 2  # target + other (inactive excluded)
    assert inactive["identifier"] in fleet["skipped_inactive"]


def test_demo_generate_batch_limit(client, create_machine, monkeypatch):
    from types import SimpleNamespace

    create_machine("SIM-9")
    create_machine("SIM-10")
    monkeypatch.setattr(
        "app.services.simulation.get_settings",
        lambda: SimpleNamespace(simulation_seed=42, simulation_max_batch=5),
    )

    response = client.post("/api/v1/demo/generate", json={"count": 6})
    assert response.status_code == 422
    assert "batch limit" in error_body(response.json())["message"]

    response = client.post("/api/v1/demo/generate", json={"count": 3})
    assert response.status_code == 422  # 2 machines x 3 = 6 > 5
    assert "batch limit" in error_body(response.json())["message"]


def test_demo_generate_unknown_and_inactive_explicit(client, create_machine):
    assert client.post("/api/v1/demo/generate", json={"machine_id": 999999}).status_code == 404

    machine = create_machine("SIM-11")
    assert (
        client.patch(f"/api/v1/machines/{machine['id']}", json={"status": "inactive"}).status_code
        == 200
    )
    response = client.post("/api/v1/demo/generate", json={"machine_id": machine["id"]})
    assert response.status_code == 409
    assert error_body(response.json())["code"] == "invalid_state"


def test_step_requires_machine_id(client):
    response = client.post("/api/v1/simulation/step", json={})
    assert response.status_code == 422
    assert error_body(response.json())["code"] == "validation_error"
