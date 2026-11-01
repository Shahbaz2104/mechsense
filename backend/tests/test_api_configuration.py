"""Configuration endpoint: public settings only."""

import json


def test_configuration_exposes_public_settings(client):
    response = client.get("/api/v1/configuration")
    assert response.status_code == 200
    body = response.json()

    assert body["app_name"] == "MechSense API"
    assert body["environment"] in {"development", "test", "production"}
    assert body["pagination"]["default_page_size"] == 25
    assert body["pagination"]["max_page_size"] >= 25
    assert body["imports"]["max_file_mb"] == 10
    assert body["imports"]["max_rows"] == 100_000
    assert body["simulation"]["seed"] == 42
    assert body["simulation"]["max_batch"] == 500
    assert body["simulation"]["interval_minutes"] == 5


def test_configuration_never_leaks_sensitive_settings(client):
    text = json.dumps(client.get("/api/v1/configuration").json()).lower()
    for secret in ("database", "postgres", "password", "credential", "cors", "log_level"):
        assert secret not in text, f"configuration leaked '{secret}'"
