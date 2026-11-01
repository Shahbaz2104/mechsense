"""Generator: determinism, correlations, scenario injection (no database)."""

from datetime import UTC, datetime, timedelta

from app.simulation.generator import PROFILES, generate_history, machine_rng

WINDOW_START = datetime(2026, 1, 9, 13, 0, tzinfo=UTC)  # ends at 13:00 (day-shift peak)
INTERVAL = timedelta(minutes=5)
DAYS = 7


def _history(identifier: str = "P-101", seed: int = 42, **kwargs):
    profile = PROFILES[identifier]
    defaults = {
        "machine_identifier": identifier,
        "base_seed": seed,
        "start": WINDOW_START,
        "end": WINDOW_START + timedelta(days=DAYS),
        "interval": INTERVAL,
        "has_pressure": identifier == "C-401",
    }
    defaults.update(kwargs)
    return generate_history(profile, **defaults)


def test_generation_is_deterministic():
    assert _history() == _history()


def test_different_seed_changes_data():
    assert _history(seed=1) != _history(seed=2)


def test_timestamps_are_spaced_and_cover_window():
    rows = _history()
    expected_count = int(DAYS * 24 * 60 / 5) + 1  # inclusive bounds
    assert len(rows) == expected_count
    assert rows[0]["timestamp"] == WINDOW_START
    assert rows[-1]["timestamp"] == WINDOW_START + timedelta(days=DAYS)
    deltas = {rows[i + 1]["timestamp"] - rows[i]["timestamp"] for i in range(len(rows) - 1)}
    assert deltas == {INTERVAL}


def test_pressure_only_present_when_sensor_exists():
    without = _history("P-101")
    assert all(r["pressure"] is None for r in without)
    with_pressure = _history("C-401")
    assert all(r["pressure"] is not None for r in with_pressure)


def test_shutdown_window_stops_the_shaft():
    rows = _history("M-204")
    total = (rows[-1]["timestamp"] - rows[0]["timestamp"]).total_seconds()
    shutdown = [
        r
        for r in rows
        if 0.30 <= (r["timestamp"] - rows[0]["timestamp"]).total_seconds() / total <= 0.42
    ]
    running = [r for r in rows if r not in shutdown]
    assert shutdown, "shutdown window must contain readings"
    assert max(r["rpm"] for r in shutdown) < 20
    assert min(r["rpm"] for r in running) > 500


def test_bearing_fault_vibration_leads_temperature():
    """The signature correlation: vibration climbs before temperature does."""
    rows = _history("P-101")
    thresholds = {"vibration_rms": {"warning": 4.5}, "temperature": {"warning": 75.0}}
    first_vib = next(
        r["timestamp"] for r in rows if r["vibration_rms"] >= thresholds["vibration_rms"]["warning"]
    )
    first_temp = next(
        r["timestamp"] for r in rows if r["temperature"] >= thresholds["temperature"]["warning"]
    )
    assert first_vib < first_temp, "vibration must breach before temperature"
    # fault window: last reading is clearly critical on both metrics
    assert rows[-1]["vibration_rms"] > 7.1
    assert rows[-1]["temperature"] > 90.0


def test_healthy_machine_stays_under_warning_entirely():
    rows = _history("F-301")
    assert max(r["vibration_rms"] for r in rows) < 5.0
    assert max(r["temperature"] for r in rows) < 75.0


def test_elevated_scenario_crosses_warning_not_critical():
    rows = _history("B-501")
    assert max(r["vibration_rms"] for r in rows) >= 4.0
    assert max(r["vibration_rms"] for r in rows) < 6.5


def test_spike_is_isolated_single_point():
    rows = _history("C-401")
    above = [i for i, r in enumerate(rows) if r["vibration_rms"] >= 8.0]
    assert len(above) == 1, f"expected exactly one spike, got indices {above}"
    assert rows[above[0]]["pressure"] >= 11.0


def test_load_follows_diurnal_pattern():
    rows = _history("F-301")
    hourly = {}
    for row in rows:
        hourly.setdefault(row["timestamp"].hour, []).append(row["load_pct"])
    night = min(sum(hourly[h]) / len(hourly[h]) for h in (1, 2, 3, 4))
    day = max(sum(hourly[h]) / len(hourly[h]) for h in (10, 11, 12, 13))
    assert day > night + 5, "day shift load should exceed night shift load"


def test_rng_streams_are_stable_per_machine():
    a1 = machine_rng(42, "P-101").integers(0, 1000, 10).tolist()
    a2 = machine_rng(42, "P-101").integers(0, 1000, 10).tolist()
    b = machine_rng(42, "M-204").integers(0, 1000, 10).tolist()
    assert a1 == a2
    assert a1 != b
