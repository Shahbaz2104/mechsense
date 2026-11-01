"""Detection service: event creation, dedup, escalation, edge rules (DB)."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.detection.service import process_reading
from app.models import AnomalyEvent, AnomalyStatus, Machine, MachineStatus

START = datetime(2026, 1, 15, 10, 0, tzinfo=UTC)
THRESHOLDS = {"vibration_rms": {"warning": 4.5, "critical": 7.1}}


def _machine(db: Session, **overrides) -> Machine:
    data = {
        "identifier": "DET-1",
        "name": "Detection Rig",
        "equipment_type": "pump",
        "thresholds": THRESHOLDS,
        "status": MachineStatus.active,
    }
    data.update(overrides)
    machine = Machine(**data)
    db.add(machine)
    db.flush()
    return machine


def _event_count(db: Session, machine: Machine) -> int:
    return int(
        db.scalar(
            select(func.count())
            .select_from(AnomalyEvent)
            .where(AnomalyEvent.machine_id == machine.id)
        )
        or 0
    )


def test_clean_reading_creates_nothing(db, add_reading):
    machine = _machine(db)
    reading = add_reading(machine, START, vibration=2.0)
    assert process_reading(db, reading) == []
    assert _event_count(db, machine) == 0


def test_violation_creates_open_event_with_reading_link(db, add_reading):
    machine = _machine(db)
    reading = add_reading(machine, START, vibration=9.4)
    touched = process_reading(db, reading)

    assert len(touched) == 1
    event = touched[0]
    assert event.status == AnomalyStatus.open
    assert event.severity.value == "critical"
    assert event.reading_id == reading.id
    assert event.detected_at == reading.timestamp
    assert float(event.observed_value) == 9.4
    assert "9.4" in event.explanation


def test_repeat_violation_extends_same_event(db, add_reading):
    machine = _machine(db)
    first = add_reading(machine, START, vibration=5.0)
    second = add_reading(machine, START + timedelta(minutes=5), vibration=5.5)

    process_reading(db, first)
    process_reading(db, second)

    assert _event_count(db, machine) == 1
    event = db.scalar(select(AnomalyEvent).where(AnomalyEvent.machine_id == machine.id))
    assert event.last_seen_at == second.timestamp
    assert event.observed_value == 5.5
    assert event.severity.value == "warning"  # not yet critical


def test_severity_escalates_in_place(db, add_reading):
    machine = _machine(db)
    warning_reading = add_reading(machine, START, vibration=5.0)
    critical_reading = add_reading(machine, START + timedelta(minutes=5), vibration=8.8)

    first_event = process_reading(db, warning_reading)[0]
    event_id = first_event.id
    escalated = process_reading(db, critical_reading)[0]

    assert escalated.id == event_id  # same event, not a new one
    assert escalated.severity.value == "critical"
    assert _event_count(db, machine) == 1


def test_severity_never_downgrades(db, add_reading):
    machine = _machine(db)
    critical_reading = add_reading(machine, START, vibration=9.0)
    calmer_reading = add_reading(machine, START + timedelta(minutes=5), vibration=5.0)

    process_reading(db, critical_reading)
    event = process_reading(db, calmer_reading)[0]

    assert event.severity.value == "critical"
    assert event.observed_value == 5.0  # observation refreshes, severity does not


def test_metrics_are_independent_events(db, add_reading):
    machine = _machine(
        db,
        thresholds={
            "vibration_rms": {"warning": 4.5, "critical": 7.1},
            "temperature": {"warning": 75.0, "critical": 90.0},
        },
    )
    reading = add_reading(machine, START, vibration=9.0, temperature=95.0)
    touched = process_reading(db, reading)

    assert {e.metric for e in touched} == {"vibration_rms", "temperature"}
    assert _event_count(db, machine) == 2


def test_no_event_for_inactive_machine(db, add_reading):
    machine = _machine(db, status=MachineStatus.inactive)
    reading = add_reading(machine, START, vibration=9.9)
    assert process_reading(db, reading) == []
    assert _event_count(db, machine) == 0


def test_resolved_condition_requires_fresh_edge(db, add_reading):
    """After resolve, a still-violating condition must NOT re-fire until a
    normal reading re-arms the edge; the next violation creates a new event."""
    machine = _machine(db)
    first = add_reading(machine, START, vibration=6.0)
    still_bad = add_reading(machine, START + timedelta(minutes=5), vibration=6.2)
    recovered = add_reading(machine, START + timedelta(minutes=10), vibration=2.0)
    bad_again = add_reading(machine, START + timedelta(minutes=15), vibration=6.5)

    event = process_reading(db, first)[0]
    process_reading(db, still_bad)
    assert _event_count(db, machine) == 1

    # user resolves while condition persists
    event.status = AnomalyStatus.resolved
    event.resolved_at = datetime.now(UTC)
    db.flush()

    # still violating with no active event, but previous reading also violated
    assert process_reading(db, recovered) == []  # normal reading: no event work
    assert _event_count(db, machine) == 1

    process_reading(db, bad_again)  # previous was clean -> edge -> new event
    assert _event_count(db, machine) == 2


def test_resolved_then_violating_without_recovery_does_not_refire(db, add_reading):
    machine = _machine(db)
    first = add_reading(machine, START, vibration=6.0)
    still_bad = add_reading(machine, START + timedelta(minutes=5), vibration=6.3)

    event = process_reading(db, first)[0]
    event.status = AnomalyStatus.resolved
    event.resolved_at = datetime.now(UTC)
    db.flush()

    assert process_reading(db, still_bad) == []  # continuous condition, no new edge
    assert _event_count(db, machine) == 1
