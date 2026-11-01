"""Deterministic synthetic sensor data with correlated machine physics.

Design goals (spec §8):
- Reproducible: a configurable base seed derives a stable per-machine,
  per-timestamp RNG stream (same inputs -> identical readings).
- Correlated signals (never independent noise): load drives rpm and vibration,
  temperature follows load/vibration with thermal lag, pressure follows load
  on compression equipment.
- Scenario injection: shutdown windows, a gradual bearing fault (vibration
  first, temperature lagged behind it), isolated spikes, and elevated-but-not
  critical operation — so detection has honest things to find.
- Units: vibration mm/s RMS, temperature °C, rpm, load %, pressure bar.

These are simulated demo signals, not measurements from certified equipment.
"""

import math
import zlib
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

import numpy as np

METRICS = ("vibration_rms", "temperature", "rpm", "load_pct", "pressure")

# Cadence shared by seed history, simulation step and demo generation so new
# readings continue the same 5-minute timeline.
READ_INTERVAL = timedelta(minutes=5)


@dataclass(frozen=True)
class Scenario:
    """A time-boxed behavior injected into the history window."""

    kind: str  # shutdown | fault_ramp | spike | elevated
    start: float  # fraction of window [0..1]
    end: float
    # fault_ramp: vibration/temperature extra at full progress.
    vibration_extra: float = 0.0
    temperature_extra: float = 0.0
    # spike: one-shot multipliers/additions at `at` fraction.
    at: float = 0.5
    vibration_multiplier: float = 1.0
    pressure_add: float = 0.0


@dataclass(frozen=True)
class MachineProfile:
    """Operating characteristics for one equipment type."""

    nominal_rpm: float
    load_base: float
    load_amplitude: float
    vibration_base: float
    vibration_load_gain: float
    vibration_noise: float
    ambient_temperature: float
    temperature_load_gain: float
    temperature_vibration_gain: float
    thermal_lag: float  # 0..1, larger = faster temperature response
    temperature_noise: float
    pressure_base: float | None = None  # None -> machine has no pressure sensor
    pressure_load_gain: float = 0.0
    rpm_load_gain: float = 0.06
    scenarios: tuple[Scenario, ...] = field(default_factory=tuple)


PROFILES: dict[str, MachineProfile] = {
    "P-101": MachineProfile(
        nominal_rpm=1480,
        load_base=62,
        load_amplitude=14,
        vibration_base=2.6,
        vibration_load_gain=1.6,
        vibration_noise=0.16,
        ambient_temperature=27,
        temperature_load_gain=0.42,
        temperature_vibration_gain=3.0,
        thermal_lag=0.12,
        temperature_noise=0.35,
        scenarios=(
            # Bearing wear in the final third: vibration climbs first,
            # temperature follows with a delay (physical lag, not coincidence).
            Scenario(
                kind="fault_ramp",
                start=0.66,
                end=1.0,
                vibration_extra=6.4,
                temperature_extra=20.0,
            ),
        ),
    ),
    "M-204": MachineProfile(
        nominal_rpm=1785,
        load_base=55,
        load_amplitude=18,
        vibration_base=1.9,
        vibration_load_gain=1.1,
        vibration_noise=0.12,
        ambient_temperature=28,
        temperature_load_gain=0.5,
        temperature_vibration_gain=2.6,
        thermal_lag=0.1,
        temperature_noise=0.3,
        scenarios=(
            # Planned shutdown window: shaft stops, vibration drops to idle
            # levels, temperature decays toward ambient.
            Scenario(kind="shutdown", start=0.3, end=0.42),
        ),
    ),
    "F-301": MachineProfile(
        nominal_rpm=960,
        load_base=48,
        load_amplitude=10,
        vibration_base=3.1,
        vibration_load_gain=1.3,
        vibration_noise=0.2,
        ambient_temperature=30,
        temperature_load_gain=0.48,
        temperature_vibration_gain=2.2,
        thermal_lag=0.14,
        temperature_noise=0.4,
        scenarios=(),  # the healthy reference machine
    ),
    "C-401": MachineProfile(
        nominal_rpm=2950,
        load_base=70,
        load_amplitude=12,
        vibration_base=3.2,
        vibration_load_gain=1.2,
        vibration_noise=0.18,
        ambient_temperature=31,
        temperature_load_gain=0.42,
        temperature_vibration_gain=2.4,
        thermal_lag=0.11,
        temperature_noise=0.35,
        pressure_base=6.4,
        pressure_load_gain=0.018,
        scenarios=(
            # Single-point pressure/vibration excursion (one bad reading),
            # then the process settles again. Amplitudes are sized so the
            # spike crosses CRITICAL regardless of the load phase that hour.
            Scenario(
                kind="spike",
                start=0.78,
                end=0.78,
                at=0.78,
                vibration_multiplier=3.0,
                pressure_add=4.5,
            ),
        ),
    ),
    "B-501": MachineProfile(
        nominal_rpm=3000,
        load_base=40,
        load_amplitude=8,
        vibration_base=2.2,
        vibration_load_gain=0.9,
        vibration_noise=0.12,
        ambient_temperature=26,
        temperature_load_gain=0.4,
        temperature_vibration_gain=2.4,
        thermal_lag=0.13,
        temperature_noise=0.3,
        scenarios=(
            # Sustained elevated vibration: crosses warning, stays under
            # critical — demonstrates warning-only events.
            Scenario(
                kind="elevated",
                start=0.86,
                end=1.0,
                vibration_extra=2.6,
                temperature_extra=6.0,
            ),
        ),
    ),
}


def machine_rng(base_seed: int, machine_identifier: str, salt: int = 0) -> np.random.Generator:
    """Stable RNG stream for a machine (crc32 keeps it independent of PYTHONHASHSEED)."""
    key = [int(base_seed), zlib.crc32(machine_identifier.encode("utf-8")), int(salt)]
    return np.random.default_rng(key)


def generate_history(
    profile: MachineProfile,
    *,
    machine_identifier: str,
    base_seed: int,
    start: datetime,
    end: datetime,
    interval: timedelta,
    has_pressure: bool,
) -> list[dict]:
    """Generate correlated readings between start and end (inclusive bounds)."""
    if end < start:
        raise ValueError("end must not be before start")
    rng = machine_rng(base_seed, machine_identifier, salt=1)

    timestamps: list[datetime] = []
    cursor = start
    while cursor <= end:
        timestamps.append(cursor)
        cursor += interval
    if not timestamps:
        return []

    total_seconds = max((timestamps[-1] - timestamps[0]).total_seconds(), 1.0)
    rows: list[dict] = []
    previous_temperature = profile.ambient_temperature + 10.0
    spike_index = _spike_index(profile, timestamps)

    for index, ts in enumerate(timestamps):
        elapsed = (ts - timestamps[0]).total_seconds()
        progress = elapsed / total_seconds
        hour = ts.hour + ts.minute / 60.0

        shutdown = _in_scenario(profile, "shutdown", progress)
        # Diurnal load pattern (day shift up, night shift down) + gentle noise.
        load = (
            profile.load_base
            + profile.load_amplitude * math.sin(2 * math.pi * (hour - 7) / 24)
            + float(rng.normal(0, 1.8))
        )
        if shutdown:
            load = max(0.0, float(rng.normal(0.4, 0.2)))

        rpm = profile.nominal_rpm * (1.0 + profile.rpm_load_gain * ((load - 50.0) / 50.0)) + float(
            rng.normal(0, profile.nominal_rpm * 0.002)
        )
        if shutdown:
            rpm = max(0.0, float(rng.normal(0, 1.5)))

        vibration = (
            profile.vibration_base
            + profile.vibration_load_gain * ((load - 50.0) / 50.0)
            + float(rng.normal(0, profile.vibration_noise))
        )
        # Slow mechanical drift over the whole window (wear progression).
        vibration += 0.35 * progress
        if shutdown:
            vibration = max(0.25, float(rng.normal(0.5, 0.06)))

        fault_progress = _scenario_progress(profile, "fault_ramp", progress)
        if fault_progress is not None:
            vibration += profile_extra(profile, "vibration") * (fault_progress**1.6)
        elevated = _in_scenario(profile, "elevated", progress)
        if elevated:
            vibration += _scenario_param(profile, "elevated", "vibration_extra")
        if index == spike_index:
            vibration *= _scenario_param(profile, "spike", "vibration_multiplier")

        vibration = max(0.1, vibration)

        temperature_target = (
            profile.ambient_temperature
            + profile.temperature_load_gain * load
            + profile.temperature_vibration_gain * vibration
        )
        fault_temp_progress = _scenario_progress(profile, "fault_ramp", progress)
        if fault_temp_progress is not None:
            # Heating lags the vibration ramp: it only takes off once the
            # ramp is already well advanced (delayed physical response).
            lagged = max(0.0, (fault_temp_progress - 0.35) / 0.65)
            temperature_target += profile_extra(profile, "temperature") * (lagged**1.3)
        if elevated:
            temperature_target += _scenario_param(profile, "elevated", "temperature_extra")
        if shutdown:
            temperature_target = profile.ambient_temperature + 6.0

        previous_temperature += profile.thermal_lag * (temperature_target - previous_temperature)
        temperature = previous_temperature + float(rng.normal(0, profile.temperature_noise))

        pressure: float | None = None
        if has_pressure and profile.pressure_base is not None:
            pressure = (
                profile.pressure_base
                + profile.pressure_load_gain * load
                + float(rng.normal(0, 0.07))
            )
            if index == spike_index:
                pressure += _scenario_param(profile, "spike", "pressure_add")

        rows.append(
            {
                "timestamp": ts,
                "vibration_rms": round(max(0.0, vibration), 3),
                "temperature": round(temperature, 2),
                "rpm": round(max(0.0, rpm), 1),
                "load_pct": round(min(100.0, max(0.0, load)), 2),
                "pressure": round(pressure, 2) if pressure is not None else None,
            }
        )
    return rows


def generate_next_reading(
    profile: MachineProfile,
    *,
    machine_identifier: str,
    base_seed: int,
    after: datetime | None,
    interval: timedelta,
    has_pressure: bool,
    now: datetime | None = None,
) -> dict:
    """Next plausible reading continuing the machine's current behavior.

    The RNG stream is derived from (seed, machine, timestamp) so repeated calls
    for the same timestamp are deterministic, while each new timestamp differs.
    """
    timestamp = now or datetime.now(UTC)
    if after is not None and timestamp <= after:
        timestamp = after + interval

    # Reuse history generation over a short trailing window so scenario logic,
    # correlations and physics stay identical to the seeded data.
    window_start = timestamp - interval * 6
    rows = generate_history(
        profile,
        machine_identifier=machine_identifier,
        base_seed=base_seed,
        start=window_start,
        end=timestamp,
        interval=interval,
        has_pressure=has_pressure,
    )
    return rows[-1]


def profile_for(identifier: str) -> MachineProfile:
    return PROFILES.get(identifier, PROFILES["F-301"])


def _scenarios(profile: MachineProfile, kind: str) -> list[Scenario]:
    return [s for s in profile.scenarios if s.kind == kind]


def _in_scenario(profile: MachineProfile, kind: str, progress: float) -> bool:
    return any(s.start <= progress <= s.end for s in _scenarios(profile, kind))


def _scenario_progress(profile: MachineProfile, kind: str, progress: float) -> float | None:
    for scenario in _scenarios(profile, kind):
        if scenario.start <= progress <= scenario.end:
            span = max(scenario.end - scenario.start, 1e-9)
            return min(1.0, max(0.0, (progress - scenario.start) / span))
    return None


def _scenario_param(profile: MachineProfile, kind: str, name: str) -> float:
    for scenario in _scenarios(profile, kind):
        return float(getattr(scenario, name))
    return 0.0


def profile_extra(profile: MachineProfile, unit: str) -> float:
    """Fault-ramp amplitude for vibration or temperature."""
    for scenario in _scenarios(profile, "fault_ramp"):
        if unit == "vibration":
            return scenario.vibration_extra
        return scenario.temperature_extra
    return 0.0


def _spike_index(profile: MachineProfile, timestamps: list[datetime]) -> int | None:
    spikes = _scenarios(profile, "spike")
    if not spikes or not timestamps:
        return None
    at = spikes[0].at
    return min(int(at * (len(timestamps) - 1)), len(timestamps) - 1)
