"""Machine endpoints: CRUD, filters, sorting, pagination, health filter."""

from tests.conftest import error_body


def test_list_empty_database_returns_empty_page(client):
    body = client.get("/api/v1/machines").json()
    assert body == {"items": [], "total": 0, "page": 1, "page_size": 25, "pages": 0}


def test_create_machine_returns_201_and_normalizes_identifier(client, machine_payload):
    response = client.post("/api/v1/machines", json=machine_payload("p-104"))
    assert response.status_code == 201
    body = response.json()
    assert body["identifier"] == "P-104"  # uppercased
    assert body["status"] == "active"
    assert body["thresholds"]["vibration_rms"] == {"warning": 4.5, "critical": 7.1}
    assert body["id"] >= 1


def test_create_duplicate_identifier_conflicts(client, machine_payload):
    client.post("/api/v1/machines", json=machine_payload("DUP-1"))
    response = client.post("/api/v1/machines", json=machine_payload("dup-1"))
    assert response.status_code == 409
    error = error_body(response.json())
    assert error["code"] == "conflict"
    assert "DUP-1" in error["message"]


def test_create_invalid_equipment_type_is_422_with_envelope(client, machine_payload):
    response = client.post(
        "/api/v1/machines", json=machine_payload("BAD-1", equipment_type="rocket")
    )
    assert response.status_code == 422
    error = error_body(response.json())
    assert error["code"] == "validation_error"
    assert error["details"]


def test_get_machine_detail_and_404(client, create_machine):
    machine = create_machine("DET-9")
    found = client.get(f"/api/v1/machines/{machine['id']}")
    assert found.status_code == 200
    assert found.json()["name"] == machine["name"]

    missing = client.get("/api/v1/machines/424242")
    assert missing.status_code == 404
    assert error_body(missing.json())["code"] == "not_found"


def test_patch_machine_updates_fields(client, create_machine):
    machine = create_machine("UPD-1")
    response = client.patch(
        f"/api/v1/machines/{machine['id']}",
        json={
            "name": "Renamed Rig",
            "thresholds": {"temperature": {"warning": 70, "critical": 85}},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Renamed Rig"
    assert body["thresholds"] == {"temperature": {"warning": 70.0, "critical": 85.0}}
    assert body["identifier"] == "UPD-1"  # untouched


def test_patch_identifier_conflict(client, create_machine):
    create_machine("CFL-1")
    other = create_machine("CFL-2")
    response = client.patch(f"/api/v1/machines/{other['id']}", json={"identifier": "cfl-1"})
    assert response.status_code == 409
    assert error_body(response.json())["code"] == "conflict"


def test_patch_unknown_machine_is_404(client):
    response = client.patch("/api/v1/machines/999", json={"name": "x"})
    assert response.status_code == 404


def test_pagination_and_pages_count(client, create_machine):
    for i in range(5):
        create_machine(f"PG-{i}")
    page1 = client.get("/api/v1/machines?page=1&page_size=2&sort=identifier").json()
    page3 = client.get("/api/v1/machines?page=3&page_size=2&sort=identifier").json()
    beyond = client.get("/api/v1/machines?page=9&page_size=2").json()

    assert page1["total"] == 5 and page1["pages"] == 3
    assert len(page1["items"]) == 2
    assert [m["identifier"] for m in page1["items"]] == ["PG-0", "PG-1"]
    assert [m["identifier"] for m in page3["items"]] == ["PG-4"]
    assert beyond["items"] == []


def test_sort_order_descending(client, create_machine):
    for ident in ["A-1", "C-3", "B-2"]:
        create_machine(ident)
    body = client.get("/api/v1/machines?sort=identifier&order=desc").json()
    assert [m["identifier"] for m in body["items"]] == ["C-3", "B-2", "A-1"]


def test_invalid_sort_field_rejected(client):
    response = client.get("/api/v1/machines?sort=drop_table")
    assert response.status_code == 422
    error = error_body(response.json())
    assert error["code"] == "validation_error"


def test_search_is_case_insensitive_substring(client, create_machine):
    create_machine("SEA-1", name="Cooling Pump Alpha")
    create_machine("SEA-2", name="Extraction Fan Beta")
    body = client.get("/api/v1/machines?search=cooling").json()
    assert [m["identifier"] for m in body["items"]] == ["SEA-1"]
    by_id = client.get("/api/v1/machines?search=sea-2").json()
    assert [m["identifier"] for m in by_id["items"]] == ["SEA-2"]


def test_filter_by_equipment_type_and_status(client, create_machine, machine_payload):
    create_machine("FLT-1", equipment_type="compressor")
    create_machine("FLT-2", equipment_type="pump")
    pumps = client.get("/api/v1/machines?equipment_type=pump").json()
    assert [m["identifier"] for m in pumps["items"]] == ["FLT-2"]

    inactive = create_machine("FLT-3")
    client.patch(f"/api/v1/machines/{inactive['id']}", json={"status": "inactive"})
    active = client.get("/api/v1/machines?status=active").json()
    off = client.get("/api/v1/machines?status=inactive").json()
    assert active["total"] == 2 and off["total"] == 1


def test_health_filter_matches_python_derivation(client, create_machine, ingest):
    """SQL-side health filter must agree with the health_status we return."""
    # no_data: fresh machine without readings
    create_machine("HL-1")
    # healthy: normal readings under thresholds
    healthy = create_machine("HL-2")
    ingest(healthy["id"], timestamp="2026-01-15T10:00:00Z", vibration_rms=1.5)
    ingest(healthy["id"], timestamp="2026-01-15T10:05:00Z", vibration_rms=1.7)
    # critical: violating reading creates an open critical event
    critical = create_machine("HL-3")
    ingest(critical["id"], timestamp="2026-01-15T10:00:00Z", vibration_rms=9.5)
    # inactive: deactivated regardless of readings
    inactive = create_machine("HL-4")
    client.patch(f"/api/v1/machines/{inactive['id']}", json={"status": "inactive"})

    all_machines = client.get("/api/v1/machines?page_size=100").json()["items"]
    for health in ["healthy", "no_data", "critical", "inactive", "warning"]:
        filtered = client.get(f"/api/v1/machines?health={health}&page_size=100").json()["items"]
        expected = sorted(m["identifier"] for m in all_machines if m["health_status"] == health)
        assert sorted(m["identifier"] for m in filtered) == expected, f"health={health}"

    by_health = {m["identifier"]: m["health_status"] for m in all_machines}
    assert by_health == {
        "HL-1": "no_data",
        "HL-2": "healthy",
        "HL-3": "critical",
        "HL-4": "inactive",
    }


def test_health_warning_from_resolved_event_still_violating_reading(client, create_machine, ingest):
    """No open event + latest reading over warning -> warning (edge rule)."""
    machine = create_machine("HLW-1")
    ingest(machine["id"], timestamp="2026-01-15T10:00:00Z", vibration_rms=5.5)  # warning event
    events = client.get(f"/api/v1/anomalies?machine_id={machine['id']}").json()["items"]
    assert len(events) == 1
    client.post(f"/api/v1/anomalies/{events[0]['id']}/resolve")

    body = client.get("/api/v1/machines?search=HLW-1").json()
    assert body["items"][0]["health_status"] == "warning"


def test_list_items_expose_health_context_fields(client, create_machine, ingest):
    machine = create_machine("CTX-1")
    ingest(machine["id"], timestamp="2026-01-15T10:00:00Z", vibration_rms=9.9)
    item = client.get("/api/v1/machines?search=CTX-1").json()["items"][0]
    assert item["health_status"] == "critical"
    assert item["latest_reading_at"] == "2026-01-15T10:00:00Z"
    assert item["vibration_rms"] == 9.9
    assert item["open_anomaly_count"] == 1
    assert item["latest_anomaly"]["metric"] == "vibration_rms"
