"""Anomaly endpoints: listing filters, detail shape, lifecycle rules."""

from tests.conftest import error_body


def _seed_events(client, create_machine, ingest):
    """Three events: critical vibration (open), warning temperature, then a warning elsewhere."""
    machine = create_machine(
        "AN-1",
        thresholds={
            "vibration_rms": {"warning": 4.5, "critical": 7.1},
            "temperature": {"warning": 75.0, "critical": 90.0},
        },
    )
    ingest(machine["id"], timestamp="2026-01-14T10:00:00Z", vibration_rms=9.0)
    ingest(machine["id"], timestamp="2026-01-15T10:00:00Z", temperature=80.0)  # warning only
    other = create_machine("AN-2", thresholds={"vibration_rms": {"warning": 4.5, "critical": 7.1}})
    ingest(other["id"], timestamp="2026-01-15T10:00:00Z", vibration_rms=5.0)
    return machine, other


def test_list_returns_page_with_machine_and_reading_refs(client, create_machine, ingest):
    machine = create_machine("AN-L1")
    ingest(machine["id"], timestamp="2026-01-15T10:00:00Z", vibration_rms=9.2)
    body = client.get("/api/v1/anomalies").json()
    assert body["total"] == 1
    item = body["items"][0]
    assert item["machine"]["identifier"] == "AN-L1"
    assert item["reading"]["timestamp"] == "2026-01-15T10:00:00Z"
    assert item["observed_value"] == 9.2
    assert item["threshold_value"] == 7.1
    assert item["status"] == "open"
    assert "critical" in item["explanation"].lower()


def test_filters_by_severity_status_metric_and_machine(client, create_machine, ingest):
    _seed_events(client, create_machine, ingest)
    critical = client.get("/api/v1/anomalies?severity=critical").json()
    assert critical["total"] == 1
    warning = client.get("/api/v1/anomalies?severity=warning").json()
    assert warning["total"] == 2
    by_metric = client.get("/api/v1/anomalies?metric=temperature").json()
    assert by_metric["total"] == 1
    open_only = client.get("/api/v1/anomalies?status=open").json()
    assert open_only["total"] == 3
    resolved = client.get("/api/v1/anomalies?status=resolved").json()
    assert resolved["total"] == 0


def test_date_range_filter(client, create_machine, ingest):
    _seed_events(client, create_machine, ingest)
    body = client.get("/api/v1/anomalies?start=2026-01-15T00:00:00Z").json()
    assert body["total"] == 2
    body = client.get("/api/v1/anomalies?end=2026-01-14T23:59:59Z").json()
    assert body["total"] == 1


def test_detail_and_404(client, create_machine, ingest):
    machine = create_machine("AN-D1")
    ingest(machine["id"], timestamp="2026-01-15T10:00:00Z", vibration_rms=8.8)
    event_id = client.get("/api/v1/anomalies").json()["items"][0]["id"]

    detail = client.get(f"/api/v1/anomalies/{event_id}").json()
    assert detail["id"] == event_id
    assert detail["reading"] is not None
    assert detail["machine"]["identifier"] == "AN-D1"

    missing = client.get("/api/v1/anomalies/555555")
    assert missing.status_code == 404
    assert error_body(missing.json())["code"] == "not_found"


def test_acknowledge_open_event(client, create_machine, ingest):
    machine = create_machine("AN-A1")
    ingest(machine["id"], timestamp="2026-01-15T10:00:00Z", vibration_rms=8.0)
    event_id = client.get("/api/v1/anomalies").json()["items"][0]["id"]

    response = client.post(
        f"/api/v1/anomalies/{event_id}/acknowledge", json={"notes": "looking into it"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "acknowledged"
    assert body["acknowledged_at"] is not None
    assert body["resolved_at"] is None
    assert body["notes"] == "looking into it"


def test_acknowledge_is_idempotent_while_acknowledged(client, create_machine, ingest):
    machine = create_machine("AN-A2")
    ingest(machine["id"], timestamp="2026-01-15T10:00:00Z", vibration_rms=8.0)
    event_id = client.get("/api/v1/anomalies").json()["items"][0]["id"]
    first = client.post(f"/api/v1/anomalies/{event_id}/acknowledge").json()
    second = client.post(
        f"/api/v1/anomalies/{event_id}/acknowledge", json={"notes": "updated note"}
    ).json()
    assert second["status"] == "acknowledged"
    assert second["acknowledged_at"] == first["acknowledged_at"]
    assert second["notes"] == "updated note"


def test_resolve_from_open_keeps_ack_null(client, create_machine, ingest):
    machine = create_machine("AN-R1")
    ingest(machine["id"], timestamp="2026-01-15T10:00:00Z", vibration_rms=8.0)
    event_id = client.get("/api/v1/anomalies").json()["items"][0]["id"]

    body = client.post(
        f"/api/v1/anomalies/{event_id}/resolve", json={"notes": "root caused"}
    ).json()
    assert body["status"] == "resolved"
    assert body["resolved_at"] is not None
    assert body["acknowledged_at"] is None  # resolved straight from open


def test_resolve_from_acknowledged_preserves_ack_timestamp(client, create_machine, ingest):
    machine = create_machine("AN-R2")
    ingest(machine["id"], timestamp="2026-01-15T10:00:00Z", vibration_rms=8.0)
    event_id = client.get("/api/v1/anomalies").json()["items"][0]["id"]
    acked = client.post(f"/api/v1/anomalies/{event_id}/acknowledge").json()
    resolved = client.post(f"/api/v1/anomalies/{event_id}/resolve").json()
    assert resolved["acknowledged_at"] == acked["acknowledged_at"]
    assert resolved["resolved_at"] is not None


def test_acknowledge_after_resolve_conflicts(client, create_machine, ingest):
    machine = create_machine("AN-R3")
    ingest(machine["id"], timestamp="2026-01-15T10:00:00Z", vibration_rms=8.0)
    event_id = client.get("/api/v1/anomalies").json()["items"][0]["id"]
    client.post(f"/api/v1/anomalies/{event_id}/resolve")

    response = client.post(f"/api/v1/anomalies/{event_id}/acknowledge")
    assert response.status_code == 409
    assert error_body(response.json())["code"] == "invalid_state"


def test_resolve_after_resolve_is_idempotent(client, create_machine, ingest):
    machine = create_machine("AN-R4")
    ingest(machine["id"], timestamp="2026-01-15T10:00:00Z", vibration_rms=8.0)
    event_id = client.get("/api/v1/anomalies").json()["items"][0]["id"]
    client.post(f"/api/v1/anomalies/{event_id}/resolve")
    again = client.post(f"/api/v1/anomalies/{event_id}/resolve", json={"notes": "closing note"})
    assert again.status_code == 200
    assert again.json()["status"] == "resolved"
    assert again.json()["notes"] == "closing note"


def test_lifecycle_actions_on_unknown_event_are_404(client):
    assert client.post("/api/v1/anomalies/424242/acknowledge").status_code == 404
    assert client.post("/api/v1/anomalies/424242/resolve").status_code == 404


def test_acknowledged_events_leave_active_alert_count(client, create_machine, ingest):
    """Open = unacknowledged alert; acknowledging removes it from the alert count."""
    machine = create_machine("AN-C1")
    ingest(machine["id"], timestamp="2026-01-15T10:00:00Z", vibration_rms=8.0)
    event_id = client.get("/api/v1/anomalies").json()["items"][0]["id"]

    before = client.get("/api/v1/dashboard/summary?period=24h").json()["summary"]["active_alerts"]
    assert before == 1
    client.post(f"/api/v1/anomalies/{event_id}/acknowledge")
    after = client.get("/api/v1/dashboard/summary?period=24h").json()["summary"]["active_alerts"]
    assert after == 0


def test_search_matches_explanation_and_machine_identity(client, create_machine, ingest):
    _seed_events(client, create_machine, ingest)
    by_identifier = client.get("/api/v1/anomalies?q=AN-2").json()
    assert by_identifier["total"] == 1
    assert by_identifier["items"][0]["machine"]["identifier"] == "AN-2"

    by_explanation = client.get("/api/v1/anomalies?q=vibration").json()
    assert by_explanation["total"] == 2  # both vibration events, any machine

    none = client.get("/api/v1/anomalies?q=zzz-no-match").json()
    assert none["total"] == 0


def test_search_combines_with_filters(client, create_machine, ingest):
    _seed_events(client, create_machine, ingest)
    body = client.get("/api/v1/anomalies?q=AN-1&metric=vibration_rms").json()
    assert body["total"] == 1
    assert body["items"][0]["metric"] == "vibration_rms"


def test_sort_by_severity_desc_puts_critical_first(client, create_machine, ingest):
    _seed_events(client, create_machine, ingest)
    body = client.get("/api/v1/anomalies?sort=severity&order=desc").json()
    severities = [item["severity"] for item in body["items"]]
    assert severities == ["critical", "warning", "warning"]

    body = client.get("/api/v1/anomalies?sort=severity&order=asc").json()
    severities = [item["severity"] for item in body["items"]]
    assert severities[0] == "warning"
    assert "critical" in severities


def test_sort_by_metric_is_deterministic(client, create_machine, ingest):
    _seed_events(client, create_machine, ingest)
    body = client.get("/api/v1/anomalies?sort=metric&order=asc").json()
    metrics = [item["metric"] for item in body["items"]]
    assert metrics == sorted(metrics)


def test_invalid_sort_rejected(client):
    response = client.get("/api/v1/anomalies?sort=columns")
    assert response.status_code == 422
    assert error_body(response.json())["code"] == "validation_error"
