"""Trend analytics endpoint: buckets, summary stats, filters, validation."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from tests.conftest import error_body

WINDOW_START = datetime(2026, 3, 1, 0, 0, tzinfo=UTC)


def _trends(client, **params):
    return client.get("/api/v1/analytics/trends", params=params)


def test_buckets_summary_and_series(client, create_machine, add_reading):
    machine = create_machine("TREND-1")
    m = SimpleNamespace(id=machine["id"])
    add_reading(m, WINDOW_START + timedelta(minutes=5), vibration=2.0)
    add_reading(m, WINDOW_START + timedelta(minutes=10), vibration=4.0)
    add_reading(m, WINDOW_START + timedelta(minutes=40), vibration=6.0)
    add_reading(m, WINDOW_START + timedelta(minutes=70), vibration=8.0)

    response = _trends(
        client,
        metric="vibration_rms",
        machine_id=machine["id"],
        start=WINDOW_START.isoformat(),
        end=(WINDOW_START + timedelta(hours=2)).isoformat(),
        buckets=4,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["metric"] == "vibration_rms"
    assert body["unit"] == "mm/s"
    assert body["bucket_seconds"] == 1800.0
    assert body["machine_id"] == machine["id"]

    summary = body["summary"]
    assert summary["reading_count"] == 4
    assert summary["min"] == 2.0
    assert summary["max"] == 8.0
    assert summary["avg"] == 5.0
    assert summary["p95"] == 7.7  # linear interpolation over [2,4,6,8]

    assert len(body["series"]) == 1
    series = body["series"][0]
    assert series["machine_identifier"] == "TREND-1"
    points = series["points"]
    assert len(points) == 3  # fourth bucket is empty -> omitted (missing data)
    assert points[0]["count"] == 2 and points[0]["avg"] == 3.0
    assert points[0]["bucket_start"].startswith("2026-03-01T00:00:00")
    assert points[1]["count"] == 1 and points[1]["max"] == 6.0
    assert points[2]["count"] == 1 and points[2]["min"] == 8.0


def test_fleet_default_window_and_multi_series(client, create_machine, add_reading):
    first = create_machine("TREND-2")
    second = create_machine("TREND-3")
    now = datetime.now(UTC)
    add_reading(SimpleNamespace(id=first["id"]), now - timedelta(hours=1), vibration=3.0)
    add_reading(SimpleNamespace(id=second["id"]), now - timedelta(hours=2), vibration=5.0)

    body = _trends(client).json()  # defaults: vibration, last 24h, all machines
    assert body["start"] < body["end"]
    assert [s["machine_identifier"] for s in body["series"]] == ["TREND-2", "TREND-3"]
    assert body["summary"]["reading_count"] == 2


def test_metric_units_and_pressure_filtering(client, create_machine, add_reading):
    machine = create_machine("TREND-4")
    m = SimpleNamespace(id=machine["id"])
    add_reading(m, WINDOW_START + timedelta(minutes=1), vibration=3.0)  # no pressure
    add_reading(m, WINDOW_START + timedelta(minutes=6), vibration=3.0, pressure=4.2)
    add_reading(m, WINDOW_START + timedelta(minutes=11), vibration=3.0, pressure=5.1)

    pressure = _trends(
        client,
        metric="pressure",
        start=WINDOW_START.isoformat(),
        end=(WINDOW_START + timedelta(hours=1)).isoformat(),
    ).json()
    assert pressure["unit"] == "bar"
    assert pressure["summary"]["reading_count"] == 2  # NULL pressure rows excluded
    assert pressure["summary"]["max"] == 5.1

    temperature = _trends(client, metric="temperature").json()
    assert temperature["unit"] == "°C"


def test_empty_window_returns_zero_summary(client, create_machine):
    create_machine("TREND-5")
    body = _trends(
        client,
        start=WINDOW_START.isoformat(),
        end=(WINDOW_START + timedelta(hours=1)).isoformat(),
    ).json()
    assert body["summary"]["reading_count"] == 0
    assert body["summary"]["avg"] is None
    assert body["series"] == []


def test_trends_validation_errors(client, create_machine):
    machine = create_machine("TREND-6")
    assert _trends(client, machine_id=999999).status_code == 404

    response = _trends(
        client,
        start=(WINDOW_START + timedelta(hours=2)).isoformat(),
        end=WINDOW_START.isoformat(),
    )
    assert response.status_code == 422
    assert "start must be before end" in error_body(response.json())["message"]

    assert _trends(client, metric="flow_rate").status_code == 422
    assert _trends(client, buckets=1).status_code == 422
    assert _trends(client, machine_id=machine["id"], buckets=999).status_code == 422


def test_trends_naive_timestamps_treated_as_utc(client, create_machine, add_reading):
    machine = create_machine("TREND-7")
    add_reading(SimpleNamespace(id=machine["id"]), WINDOW_START + timedelta(minutes=3))

    naive_start = WINDOW_START.replace(tzinfo=None).isoformat()  # naive "2026-03-01T00:00:00"
    response = _trends(
        client,
        start=naive_start,
        end=(WINDOW_START + timedelta(hours=1)).isoformat(),
    )
    assert response.status_code == 200
    assert response.json()["summary"]["reading_count"] == 1
