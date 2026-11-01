"""Maintenance endpoints: CRUD, filters, lifecycle rules, anomaly linking."""

from datetime import date, timedelta

from tests.conftest import error_body


def _create(client, title="Investigate vibration", **overrides) -> dict:
    payload = {"title": title, "scheduled_date": date.today().isoformat()}
    payload.update(overrides)
    response = client.post("/api/v1/maintenance", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_returns_work_order_number_and_machine_ref(client, create_machine):
    machine = create_machine("MT-1")
    body = _create(client, machine_id=machine["id"], priority="high")
    assert body["work_order_number"] == "WO-0001"
    assert body["machine"]["identifier"] == "MT-1"
    assert body["status"] == "scheduled"
    assert body["priority"] == "high"
    assert body["anomaly_events"] == []
    assert body["started_at"] is None
    assert body["completed_at"] is None


def test_create_missing_machine_is_404(client):
    response = client.post("/api/v1/maintenance", json={"title": "x", "machine_id": 99999})
    assert response.status_code == 404
    assert error_body(response.json())["code"] == "not_found"


def test_create_requires_title(client, create_machine):
    machine = create_machine("MT-2")
    response = client.post("/api/v1/maintenance", json={"machine_id": machine["id"]})
    assert response.status_code == 422
    assert error_body(response.json())["code"] == "validation_error"


def test_detail_and_404(client, create_machine):
    machine = create_machine("MT-3")
    created = _create(client, machine_id=machine["id"])
    detail = client.get(f"/api/v1/maintenance/{created['id']}").json()
    assert detail["id"] == created["id"]
    assert client.get("/api/v1/maintenance/424242").status_code == 404


def test_list_filters_status_machine_priority_overdue_upcoming(client, create_machine, db):
    from app.models import (
        MaintenancePriority,
        MaintenanceType,
        MaintenanceWorkOrder,
        WorkOrderStatus,
    )

    machine = create_machine("MT-4")
    other = create_machine("MT-5")
    _create(client, machine_id=machine["id"], title="Upcoming", priority="low")
    _create(client, machine_id=machine["id"], title="Due", status="in_progress")
    db.add(
        MaintenanceWorkOrder(
            work_order_number="WO-OLD",
            machine_id=other["id"],
            title="Overdue job",
            maintenance_type=MaintenanceType.corrective,
            priority=MaintenancePriority.urgent,
            status=WorkOrderStatus.scheduled,
            scheduled_date=date.today() - timedelta(days=2),
        )
    )
    db.commit()

    assert client.get("/api/v1/maintenance?status=in_progress").json()["total"] == 1
    assert client.get(f"/api/v1/maintenance?machine_id={machine['id']}").json()["total"] == 2
    assert client.get("/api/v1/maintenance?priority=urgent").json()["total"] == 1

    overdue = client.get("/api/v1/maintenance?overdue=true").json()
    assert overdue["total"] == 1
    assert overdue["items"][0]["title"] == "Overdue job"

    upcoming = client.get("/api/v1/maintenance?upcoming=true").json()
    assert upcoming["total"] == 1
    assert upcoming["items"][0]["title"] == "Upcoming"


def test_lifecycle_progression_sets_timestamps(client, create_machine):
    machine = create_machine("MT-6")
    created = _create(client, machine_id=machine["id"])

    started = client.patch(
        f"/api/v1/maintenance/{created['id']}", json={"status": "in_progress"}
    ).json()
    assert started["status"] == "in_progress"
    assert started["started_at"] is not None
    assert started["completed_at"] is None

    done = client.patch(f"/api/v1/maintenance/{created['id']}", json={"status": "completed"})
    assert done.status_code == 200
    assert done.json()["status"] == "completed"
    assert done.json()["completed_at"] is not None
    assert done.json()["started_at"] is not None


def test_terminal_state_rejects_transitions(client, create_machine):
    machine = create_machine("MT-7")
    created = _create(client, machine_id=machine["id"], status="completed")
    assert created["completed_at"] is not None

    response = client.patch(f"/api/v1/maintenance/{created['id']}", json={"status": "scheduled"})
    assert response.status_code == 409
    assert error_body(response.json())["code"] == "invalid_state"

    response = client.patch(f"/api/v1/maintenance/{created['id']}", json={"status": "in_progress"})
    assert response.status_code == 409


def test_same_status_patch_is_idempotent_field_update(client, create_machine):
    machine = create_machine("MT-8")
    created = _create(client, machine_id=machine["id"])
    again = client.patch(
        f"/api/v1/maintenance/{created['id']}",
        json={"status": "scheduled", "technician": "Dana", "title": "Retitled"},
    )
    assert again.status_code == 200
    body = again.json()
    assert body["status"] == "scheduled"
    assert body["technician"] == "Dana"
    assert body["title"] == "Retitled"


def test_link_and_unlink_anomaly_events(client, create_machine, ingest):
    machine = create_machine(
        "MT-9", thresholds={"vibration_rms": {"warning": 4.5, "critical": 7.1}}
    )
    ingest(machine["id"], timestamp="2026-01-15T10:00:00Z", vibration_rms=9.4)
    event_id = client.get("/api/v1/anomalies").json()["items"][0]["id"]

    created = _create(client, machine_id=machine["id"], anomaly_event_ids=[event_id])
    assert [e["id"] for e in created["anomaly_events"]] == [event_id]
    assert created["anomaly_events"][0]["metric"] == "vibration_rms"

    # unlink
    unlinked = client.patch(
        f"/api/v1/maintenance/{created['id']}", json={"anomaly_event_ids": []}
    ).json()
    assert unlinked["anomaly_events"] == []

    # missing event -> 404
    response = client.post(
        "/api/v1/maintenance",
        json={"title": "x", "machine_id": machine["id"], "anomaly_event_ids": [999999]},
    )
    assert response.status_code == 404


def test_linking_event_from_other_machine_is_422(client, create_machine, ingest):
    machine = create_machine("MT-10")
    other = create_machine("MT-11", thresholds={"vibration_rms": {"warning": 4.5, "critical": 7.1}})
    ingest(other["id"], timestamp="2026-01-15T10:00:00Z", vibration_rms=8.5)
    event_id = client.get("/api/v1/anomalies").json()["items"][0]["id"]

    response = client.post(
        "/api/v1/maintenance",
        json={"title": "x", "machine_id": machine["id"], "anomaly_event_ids": [event_id]},
    )
    assert response.status_code == 422
    details = error_body(response.json())["details"]
    assert details and details[0]["field"] == "anomaly_event_ids"


def test_pagination_and_sort(client, create_machine):
    machine = create_machine("MT-12")
    for day in range(5):
        _create(
            client,
            machine_id=machine["id"],
            title=f"Job {day}",
            scheduled_date=(date.today() + timedelta(days=day)).isoformat(),
        )

    page = client.get("/api/v1/maintenance?page=2&page_size=2").json()
    assert page["total"] == 5
    assert page["pages"] == 3
    assert len(page["items"]) == 2

    desc = client.get("/api/v1/maintenance?sort=scheduled_date&order=desc").json()
    titles = [item["title"] for item in desc["items"]]
    assert titles[0] == "Job 4"

    bad = client.get("/api/v1/maintenance?sort=machine_id")
    assert bad.status_code == 422
