"""Reading endpoints: ingestion lifecycle, validation, listing filters."""

from tests.conftest import error_body


def test_ingest_returns_reading_and_no_events_for_clean_data(client, create_machine, ingest):
    machine = create_machine("RD-1")
    result = ingest(machine["id"], timestamp="2026-01-15T10:00:00Z")
    assert result["status"] == 201
    body = result["body"]
    assert body["reading"]["machine_id"] == machine["id"]
    assert body["reading"]["source"] == "live"
    assert body["affected_anomaly_ids"] == []


def test_ingest_violation_triggers_detection(client, create_machine, ingest):
    machine = create_machine("RD-2")
    result = ingest(machine["id"], timestamp="2026-01-15T10:00:00Z", vibration_rms=9.4)
    assert result["status"] == 201
    assert len(result["body"]["affected_anomaly_ids"]) == 1

    events = client.get(f"/api/v1/anomalies?machine_id={machine['id']}").json()
    assert events["total"] == 1
    assert events["items"][0]["severity"] == "critical"
    assert events["items"][0]["observed_value"] == 9.4


def test_ingest_duplicate_timestamp_conflicts(client, create_machine, ingest):
    machine = create_machine("RD-3")
    ingest(machine["id"], timestamp="2026-01-15T10:00:00Z")
    duplicate = ingest(machine["id"], timestamp="2026-01-15T10:00:00Z", vibration_rms=3.0)
    assert duplicate["status"] == 409
    assert error_body(duplicate["body"])["code"] == "conflict"


def test_ingest_unknown_machine_is_404(client, ingest):
    result = ingest(9999)
    assert result["status"] == 404
    assert error_body(result["body"])["code"] == "not_found"


def test_ingest_invalid_values_are_422(client, create_machine):
    machine = create_machine("RD-4")
    response = client.post(
        "/api/v1/readings",
        json={
            "machine_id": machine["id"],
            "vibration_rms": -1,
            "temperature": 50,
            "rpm": 1500,
            "load_pct": 150,
        },
    )
    assert response.status_code == 422
    assert error_body(response.json())["code"] == "validation_error"


def test_naive_timestamp_is_interpreted_as_utc(client, create_machine, ingest):
    machine = create_machine("RD-5")
    result = ingest(machine["id"], timestamp="2026-01-15T10:00:00")
    assert result["body"]["reading"]["timestamp"] == "2026-01-15T10:00:00Z"


def test_listing_filters_and_order(client, create_machine, ingest):
    machine = create_machine("RD-6")
    ingest(machine["id"], timestamp="2026-01-15T09:00:00Z", vibration_rms=1.0)
    ingest(machine["id"], timestamp="2026-01-15T10:00:00Z", vibration_rms=2.0)
    ingest(machine["id"], timestamp="2026-01-15T11:00:00Z", vibration_rms=3.0)

    newest = client.get(f"/api/v1/readings?machine_id={machine['id']}").json()
    assert [r["vibration_rms"] for r in newest["items"]] == [3.0, 2.0, 1.0]

    oldest = client.get(f"/api/v1/readings?machine_id={machine['id']}&order=asc").json()
    assert [r["vibration_rms"] for r in oldest["items"]] == [1.0, 2.0, 3.0]

    window = client.get(
        f"/api/v1/readings?machine_id={machine['id']}"
        "&start=2026-01-15T09:30:00Z&end=2026-01-15T10:30:00Z"
    ).json()
    assert window["total"] == 1
    assert window["items"][0]["vibration_rms"] == 2.0

    empty = client.get(
        f"/api/v1/readings?machine_id={machine['id']}&start=2026-01-16T00:00:00Z"
    ).json()
    assert empty["total"] == 0


def test_machine_readings_endpoint_and_unknown_machine(client, create_machine, ingest):
    machine = create_machine("RD-7")
    ingest(machine["id"], timestamp="2026-01-15T10:00:00Z")
    response = client.get(f"/api/v1/machines/{machine['id']}/readings")
    assert response.status_code == 200
    assert response.json()["total"] == 1

    missing = client.get("/api/v1/machines/777777/readings")
    assert missing.status_code == 404
    assert error_body(missing.json())["code"] == "not_found"


def test_readings_pagination(client, create_machine, ingest):
    machine = create_machine("RD-8")
    for hour in range(5):
        ingest(machine["id"], timestamp=f"2026-01-15T{hour:02d}:00:00Z")
    body = client.get(f"/api/v1/readings?machine_id={machine['id']}&page_size=2&page=2").json()
    assert body["total"] == 5
    assert body["pages"] == 3
    assert len(body["items"]) == 2
