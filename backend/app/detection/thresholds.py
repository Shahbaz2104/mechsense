"""Phase 1 detector: transparent, configurable engineering thresholds.

Rules (documented behavior):
- A metric triggers `warning` when value >= warning threshold, `critical` when
  value >= critical threshold (critical wins when both are satisfied).
- Boundary values count as violations (>=), so a configured warning of 4.5 mm/s
  triggers at exactly 4.5 mm/s.
- Metrics without configured thresholds are ignored. Missing values (e.g.
  pressure on machines without a pressure sensor) are ignored, not errors.
- Negative readings are treated as invalid sensor data and skipped.
- Detection runs only for active machines (handled by the caller).
"""

from dataclasses import dataclass
from decimal import Decimal

# metric -> (display label, unit)
METRIC_INFO: dict[str, tuple[str, str]] = {
    "vibration_rms": ("vibration RMS", "mm/s"),
    "temperature": ("temperature", "°C"),
    "rpm": ("rotational speed", "RPM"),
    "load_pct": ("load", "%"),
    "pressure": ("pressure", "bar"),
}

THRESHOLD_METRICS: tuple[str, ...] = tuple(METRIC_INFO)

_SEVERITY_RANK = {"warning": 1, "critical": 2}


@dataclass(frozen=True)
class Violation:
    metric: str
    observed: float
    threshold: float
    severity: str  # warning | critical
    explanation: str


def _as_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def severity_rank(severity: str) -> int:
    return _SEVERITY_RANK.get(severity, 0)


def evaluate_metric(metric: str, observed: float | None, thresholds: dict) -> Violation | None:
    """Evaluate one metric against its configured thresholds."""
    if observed is None or observed < 0:
        return None
    config = thresholds.get(metric) or {}
    warning = _as_float(config.get("warning"))
    critical = _as_float(config.get("critical"))
    if warning is None and critical is None:
        return None

    severity: str | None = None
    matched: float | None = None
    if critical is not None and observed >= critical:
        severity, matched = "critical", critical
    elif warning is not None and observed >= warning:
        severity, matched = "warning", warning

    if severity is None or matched is None:
        return None

    label, unit = METRIC_INFO[metric]
    observed_text = _format_value(metric, observed)
    threshold_text = _format_value(metric, matched)
    explanation = (
        f"{severity.capitalize()}: {label} reached {observed_text} {unit} "
        f"against the configured {severity} threshold of {threshold_text} {unit}."
    )
    return Violation(
        metric=metric,
        observed=observed,
        threshold=matched,
        severity=severity,
        explanation=explanation,
    )


def evaluate_reading(reading: object, thresholds: dict) -> list[Violation]:
    """Evaluate all supported metrics of a reading; returns violations found."""
    violations: list[Violation] = []
    for metric in THRESHOLD_METRICS:
        value = _as_float(getattr(reading, metric, None))
        violation = evaluate_metric(metric, value, thresholds or {})
        if violation is not None:
            violations.append(violation)
    return violations


def _format_value(metric: str, value: float) -> str:
    """Sensible precision per metric: load/temperature two decimals, else one."""
    if metric in ("temperature", "load_pct", "pressure"):
        return f"{value:.2f}"
    if metric == "rpm":
        return f"{value:.0f}"
    return f"{value:.1f}"
