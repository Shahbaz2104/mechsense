"""Threshold detection orchestration: event creation, grouping, escalation.

Deduplication / event-grouping strategy (documented, tested):
1. At most ONE active event (status `open` or `acknowledged`) exists per
   (machine, metric, method).
2. While an active event exists, further violating readings EXTEND it:
   `last_seen_at` and `observed_value` are refreshed and the explanation is
   regenerated from the newest reading. If severity worsens (warning ->
   critical) the same event is escalated in place. Severity never downgrades.
3. With no active event, a new event is created only on an EDGE: the previous
   reading for that machine/metric must not have violated its threshold.
   This prevents a flood of new events when a condition persists after the
   user resolved the earlier event. Once readings return to normal, the next
   violation becomes a fresh edge again.
4. Non-violating readings perform no event actions — acknowledgment and
   resolution remain explicit user actions (auto-resolution is NOT done).
"""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.detection.thresholds import Violation, evaluate_metric, evaluate_reading
from app.models import (
    AnomalyEvent,
    AnomalyMethod,
    AnomalySeverity,
    AnomalyStatus,
    Machine,
    MachineStatus,
    SensorReading,
)
from app.repositories import anomalies as anomaly_repo
from app.repositories import readings as reading_repo


def process_reading(db: Session, reading: SensorReading) -> list[AnomalyEvent]:
    """Run threshold detection for one reading. Caller owns the transaction.

    Returns events that were created or extended.
    """
    machine = db.get(Machine, reading.machine_id)
    if machine is None or machine.status != MachineStatus.active:
        return []

    violations = evaluate_reading(reading, machine.thresholds or {})
    touched: list[AnomalyEvent] = []

    for violation in violations:
        active = anomaly_repo.active_event(
            db,
            machine_id=reading.machine_id,
            metric=violation.metric,
            method=AnomalyMethod.threshold,
        )
        if active is not None:
            _extend(active, reading, violation)
            touched.append(active)
            continue

        if _condition_was_active(db, reading, violation):
            # Continuous condition already reported earlier (and resolved) —
            # wait for a normal reading before allowing a new edge.
            continue

        event = AnomalyEvent(
            machine_id=reading.machine_id,
            reading_id=reading.id,
            metric=violation.metric,
            observed_value=Decimal(str(violation.observed)),
            threshold_value=Decimal(str(violation.threshold)),
            severity=AnomalySeverity(violation.severity),
            method=AnomalyMethod.threshold,
            status=AnomalyStatus.open,
            detected_at=reading.timestamp,
            last_seen_at=reading.timestamp,
            explanation=violation.explanation,
        )
        db.add(event)
        db.flush()  # autoflush is off; later readings must SEE this event
        touched.append(event)

    return touched


def _extend(event: AnomalyEvent, reading: SensorReading, violation: Violation) -> None:
    event.last_seen_at = reading.timestamp
    event.observed_value = Decimal(str(violation.observed))
    event.threshold_value = Decimal(str(violation.threshold))
    event.explanation = violation.explanation
    if violation.severity == "critical" and event.severity != AnomalySeverity.critical:
        event.severity = AnomalySeverity.critical


def _condition_was_active(db: Session, reading: SensorReading, violation: Violation) -> bool:
    """True when the immediately previous reading already violated this metric."""
    previous = reading_repo.previous_reading(
        db,
        machine_id=reading.machine_id,
        timestamp=reading.timestamp,
        exclude_reading_id=reading.id,
    )
    if previous is None:
        return False
    machine = db.get(Machine, reading.machine_id)
    thresholds = (machine.thresholds or {}) if machine else {}
    previous_value = getattr(previous, violation.metric, None)
    observed = float(previous_value) if previous_value is not None else None
    return evaluate_metric(violation.metric, observed, thresholds) is not None
