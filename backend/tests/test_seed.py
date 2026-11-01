"""Seed pipeline: reproducible demo data, designed event profile, idempotency."""

from datetime import UTC, datetime

from sqlalchemy import func, select

from app.models import AnomalyEvent, DetectionRun, Machine, MaintenanceWorkOrder, SensorReading
from app.services.seeding import DEMO_MACHINES, seed_demo_data

ANCHOR = datetime(2026, 1, 16, 13, 0, tzinfo=UTC)  # fixed window end -> reproducible
READINGS_PER_MACHINE = 7 * 24 * 12 + 1  # 7 days at 5 min, inclusive bounds


def _event_profile(db) -> dict:
    rows = db.execute(
        select(
            Machine.identifier,
            AnomalyEvent.metric,
            AnomalyEvent.severity,
            AnomalyEvent.status,
            AnomalyEvent.detected_at,
        ).join(AnomalyEvent)
    ).all()
    return {
        (identifier, metric): {
            "severity": severity.value,
            "status": status.value,
            "detected_at": detected_at,
        }
        for identifier, metric, severity, status, detected_at in rows
    }


def test_seed_builds_designed_dataset(db):
    result = seed_demo_data(db, anchor=ANCHOR)

    assert result.machines_created == len(DEMO_MACHINES) == 5
    assert result.readings_created == 5 * READINGS_PER_MACHINE
    assert result.work_orders_created == 3

    # Exactly one event per designed condition, correct severities.
    profile = _event_profile(db)
    expected_keys = {
        ("B-501", "vibration_rms"),
        ("C-401", "pressure"),
        ("C-401", "vibration_rms"),
        ("P-101", "temperature"),
        ("P-101", "vibration_rms"),
    }
    assert set(profile) == expected_keys
    assert profile[("B-501", "vibration_rms")]["severity"] == "warning"  # elevated only
    assert profile[("C-401", "pressure")]["severity"] == "critical"  # spike
    assert profile[("C-401", "vibration_rms")]["severity"] == "critical"  # spike
    assert profile[("P-101", "vibration_rms")]["severity"] == "critical"  # escalated
    assert profile[("P-101", "temperature")]["severity"] == "critical"  # escalated
    assert all(entry["status"] == "open" for entry in profile.values())

    # Correlated physics: vibration breach leads the temperature breach.
    vib_at = profile[("P-101", "vibration_rms")]["detected_at"]
    temp_at = profile[("P-101", "temperature")]["detected_at"]
    assert vib_at < temp_at

    # Healthy machines truly never breached: no events, readings under warning.
    for ident in ("F-301", "M-204"):
        assert not any(key[0] == ident for key in profile)
        machine_id = db.scalar(select(Machine.id).where(Machine.identifier == ident))
        max_vib = db.scalar(
            select(func.max(SensorReading.vibration_rms)).where(
                SensorReading.machine_id == machine_id
            )
        )
        assert float(max_vib) < 4.5

    # Corrective work order links the pump's active bearing-fault events.
    pump_id = db.scalar(select(Machine.id).where(Machine.identifier == "P-101"))
    wo = db.scalar(
        select(MaintenanceWorkOrder).where(MaintenanceWorkOrder.work_order_number == "WO-0003")
    )
    assert wo is not None
    assert len(wo.anomaly_events) == 2
    assert all(event.machine_id == pump_id for event in wo.anomaly_events)

    # Detection history is recorded for auditability.
    runs = db.scalars(select(DetectionRun)).all()
    assert len(runs) == 1
    assert runs[0].method == "threshold"
    assert runs[0].readings_processed > 0


def test_seed_rerun_is_idempotent_and_force_rebuilds(db):
    seed_demo_data(db, anchor=ANCHOR)
    readings_after_first = db.scalar(select(func.count()).select_from(SensorReading))
    events_after_first = db.scalar(select(func.count()).select_from(AnomalyEvent))
    assert readings_after_first == 5 * READINGS_PER_MACHINE

    # Plain re-run: nothing created, everything already seeded.
    second = seed_demo_data(db, anchor=ANCHOR)
    assert second.machines_created == 0
    assert second.readings_created == 0
    assert second.work_orders_created == 0
    assert sorted(second.machines_skipped) == sorted(spec.identifier for spec in DEMO_MACHINES)
    assert db.scalar(select(func.count()).select_from(SensorReading)) == readings_after_first
    assert db.scalar(select(func.count()).select_from(AnomalyEvent)) == events_after_first

    # --force: clears generated data and rebuilds the same dataset.
    forced = seed_demo_data(db, force=True, anchor=ANCHOR)
    assert forced.forced is True
    assert forced.machines_created == 0  # machine definitions preserved
    assert forced.readings_created == 5 * READINGS_PER_MACHINE
    assert db.scalar(select(func.count()).select_from(SensorReading)) == readings_after_first
    assert db.scalar(select(func.count()).select_from(AnomalyEvent)) == events_after_first
    assert len(_event_profile(db)) == events_after_first
