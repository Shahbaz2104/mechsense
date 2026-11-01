"""Dashboard summary endpoint: aggregates derived from persisted data only."""

from tests.conftest import error_body


def test_summary_on_empty_database(client):
    body = client.get("/api/v1/dashboard/summary?period=24h").json()
    summary = body["summary"]
    assert summary["total_machines"] == 0
    assert summary["active_alerts"] == 0
    assert summary["overdue_work_orders"] == 0
    assert body["machines"] == []
    period = summary["anomalies_period"]
    assert period["period_start"] < period["period_end"]


def test_summary_counts_with_mixed_health(client, create_machine, ingest, db):
    from datetime import UTC, datetime, timedelta

    from app.models import (
        MaintenancePriority,
        MaintenanceType,
        MaintenanceWorkOrder,
        WorkOrderStatus,
    )

    healthy = create_machine("DB-1")
    ingest(healthy["id"], timestamp="2026-01-15T10:00:00Z", vibration_rms=1.0)
    critical = create_machine("DB-2")
    ingest(critical["id"], timestamp="2026-01-15T10:00:00Z", vibration_rms=9.7)
    inactive = create_machine("DB-3")
    client.patch(f"/api/v1/machines/{inactive['id']}", json={"status": "inactive"})

    # one overdue + one upcoming work order
    today = datetime.now(UTC).date()
    db.add_all(
        [
            MaintenanceWorkOrder(
                work_order_number="WO-T1",
                machine_id=critical["id"],
                title="Overdue inspection",
                maintenance_type=MaintenanceType.inspection,
                priority=MaintenancePriority.high,
                status=WorkOrderStatus.scheduled,
                scheduled_date=today - timedelta(days=3),
            ),
            MaintenanceWorkOrder(
                work_order_number="WO-T2",
                machine_id=healthy["id"],
                title="Upcoming PM",
                maintenance_type=MaintenanceType.preventive,
                priority=MaintenancePriority.medium,
                status=WorkOrderStatus.scheduled,
                scheduled_date=today + timedelta(days=3),
            ),
        ]
    )
    db.commit()

    summary = client.get("/api/v1/dashboard/summary?period=24h").json()["summary"]
    assert summary["total_machines"] == 3
    assert summary["active_machines"] == 2
    assert summary["healthy_machines"] == 1
    assert summary["attention_machines"] == 1
    assert summary["inactive_machines"] == 1
    assert summary["active_alerts"] == 1
    assert summary["overdue_work_orders"] == 1
    assert summary["upcoming_work_orders"] == 1


def test_summary_machine_rows_carry_latest_anomaly(client, create_machine, ingest):
    machine = create_machine("DB-4")
    ingest(machine["id"], timestamp="2026-01-15T10:00:00Z", vibration_rms=9.1)
    body = client.get("/api/v1/dashboard/summary?period=7d").json()
    rows = {m["identifier"]: m for m in body["machines"]}
    row = rows["DB-4"]
    assert row["health_status"] == "critical"
    assert row["vibration_rms"] == 9.1
    assert row["latest_anomaly"]["severity"] == "critical"
    assert row["open_anomaly_count"] == 1


def test_anomalies_period_window_responds_to_period(client, create_machine, ingest):
    machine = create_machine("DB-5")
    ingest(machine["id"], timestamp="2026-01-15T10:00:00Z", vibration_rms=9.0)

    day = client.get("/api/v1/dashboard/summary?period=24h").json()["summary"]["anomalies_period"]
    week = client.get("/api/v1/dashboard/summary?period=7d").json()["summary"]["anomalies_period"]
    # A 24h window opens later than a 7d window (same end time).
    assert day["period_start"] > week["period_start"]
    assert day["current"] >= 0 and week["current"] >= 0


def test_invalid_period_rejected(client):
    response = client.get("/api/v1/dashboard/summary?period=forever")
    assert response.status_code == 422
    assert error_body(response.json())["code"] == "validation_error"


def test_activity_empty_database(client):
    body = client.get("/api/v1/dashboard/activity").json()
    assert body["items"] == []
    assert "generated_at" in body


def test_activity_covers_anomaly_ack_import_and_work_order(client, create_machine, ingest, db):
    from datetime import UTC, datetime

    from app.models import (
        DataImportJob,
        ImportStatus,
        MaintenancePriority,
        MaintenanceType,
        MaintenanceWorkOrder,
        WorkOrderStatus,
    )

    machine = create_machine("DB-ACT")
    ingest(machine["id"], timestamp="2026-01-15T10:00:00Z", vibration_rms=9.1)
    event_id = client.get("/api/v1/anomalies").json()["items"][0]["id"]
    client.post(f"/api/v1/anomalies/{event_id}/acknowledge", json={"notes": "checking"})

    db.add(
        DataImportJob(
            filename="line-a.csv",
            machine_id=machine["id"],
            status=ImportStatus.completed,
            total_rows=100,
            accepted_rows=97,
            rejected_rows=3,
        )
    )
    db.add(
        MaintenanceWorkOrder(
            work_order_number="WO-ACT1",
            machine_id=machine["id"],
            title="Replace bearing",
            maintenance_type=MaintenanceType.corrective,
            priority=MaintenancePriority.high,
            status=WorkOrderStatus.completed,
            scheduled_date=datetime.now(UTC).date(),
            completed_at=datetime.now(UTC),
        )
    )
    db.commit()

    items = client.get("/api/v1/dashboard/activity").json()["items"]
    kinds = [item["kind"] for item in items]
    assert "anomaly" in kinds
    assert "acknowledged" in kinds
    assert "import" in kinds
    assert "work_order" in kinds

    # newest first
    timestamps = [item["occurred_at"] for item in items]
    assert timestamps == sorted(timestamps, reverse=True)

    anomaly_item = next(i for i in items if i["kind"] == "anomaly")
    assert anomaly_item["machine_identifier"] == "DB-ACT"
    assert "vibration" in anomaly_item["title"]
    import_item = next(i for i in items if i["kind"] == "import")
    assert "line-a.csv" in import_item["title"]
    assert "97 of 100" in import_item["detail"]
    completed = [i for i in items if "completed" in i["title"]]
    assert completed and completed[0]["kind"] == "work_order"


def test_activity_respects_limit(client, create_machine, ingest):
    machine = create_machine("DB-LIM")
    ingest(machine["id"], timestamp="2026-01-14T10:00:00Z", vibration_rms=8.0)
    ingest(machine["id"], timestamp="2026-01-15T10:00:00Z", vibration_rms=9.5)

    body = client.get("/api/v1/dashboard/activity?limit=1").json()
    assert len(body["items"]) == 1
    assert body["items"][0]["kind"] == "anomaly"

    bad = client.get("/api/v1/dashboard/activity?limit=0")
    assert bad.status_code == 422
