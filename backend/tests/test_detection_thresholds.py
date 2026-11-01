"""Threshold evaluation: pure unit tests (no database)."""

import pytest

from app.detection.thresholds import evaluate_metric, evaluate_reading

THRESHOLDS = {"vibration_rms": {"warning": 4.5, "critical": 7.1}}


class TestEvaluateMetric:
    def test_warning_boundary_is_inclusive(self):
        violation = evaluate_metric("vibration_rms", 4.5, THRESHOLDS)
        assert violation is not None
        assert violation.severity == "warning"
        assert violation.threshold == 4.5

    def test_just_below_warning_is_ok(self):
        assert evaluate_metric("vibration_rms", 4.49, THRESHOLDS) is None

    def test_critical_boundary_is_inclusive(self):
        violation = evaluate_metric("vibration_rms", 7.1, THRESHOLDS)
        assert violation is not None
        assert violation.severity == "critical"

    def test_critical_wins_above_warning(self):
        violation = evaluate_metric("vibration_rms", 9.9, THRESHOLDS)
        assert violation.severity == "critical"

    def test_missing_value_never_violates(self):
        assert evaluate_metric("pressure", None, {"pressure": {"warning": 9.0}}) is None

    def test_negative_value_never_violates(self):
        assert evaluate_metric("vibration_rms", -1.0, THRESHOLDS) is None

    def test_unconfigured_metric_never_violates(self):
        assert evaluate_metric("vibration_rms", 50.0, {}) is None

    def test_warning_only_configuration(self):
        thresholds = {"temperature": {"warning": 75.0}}
        violation = evaluate_metric("temperature", 80.0, thresholds)
        assert violation.severity == "warning"
        # above warning but no critical configured -> still warning
        assert evaluate_metric("temperature", 999.0, thresholds).severity == "warning"

    def test_explanation_contains_metric_unit_and_thresholds(self):
        violation = evaluate_metric("vibration_rms", 9.9, THRESHOLDS)
        assert "vibration RMS" in violation.explanation
        assert "mm/s" in violation.explanation
        assert "7.1" in violation.explanation
        assert "critical" in violation.explanation.lower()


class TestEvaluateReading:
    def test_returns_all_violating_metrics(self):
        from app.models import SensorReading

        reading = SensorReading(
            machine_id=1,
            timestamp=None,
            vibration_rms=8.0,
            temperature=95.0,
            rpm=1500,
            load_pct=50,
            pressure=12.5,
        )
        thresholds = {
            "vibration_rms": {"warning": 4.5, "critical": 7.1},
            "temperature": {"warning": 75.0, "critical": 90.0},
            "pressure": {"warning": 9.0, "critical": 11.0},
        }
        violations = evaluate_reading(reading, thresholds)
        assert {v.metric for v in violations} == {"vibration_rms", "temperature", "pressure"}
        assert {v.severity for v in violations} == {"critical"}

    def test_clean_reading_returns_nothing(self):
        from app.models import SensorReading

        reading = SensorReading(
            machine_id=1,
            timestamp=None,
            vibration_rms=2.0,
            temperature=50.0,
            rpm=1500,
            load_pct=50,
            pressure=None,
        )
        assert evaluate_reading(reading, {"vibration_rms": {"warning": 4.5}}) == []

    @pytest.mark.parametrize(
        "metric", ["vibration_rms", "temperature", "rpm", "load_pct", "pressure"]
    )
    def test_every_known_metric_is_evaluated(self, metric):
        from app.models import SensorReading

        reading = SensorReading(
            machine_id=1,
            timestamp=None,
            vibration_rms=0.1,
            temperature=1.0,
            rpm=1.0,
            load_pct=1.0,
            pressure=1.0,
        )
        violations = evaluate_reading(reading, {metric: {"warning": 0.0}})
        assert [v.metric for v in violations] == [metric]
