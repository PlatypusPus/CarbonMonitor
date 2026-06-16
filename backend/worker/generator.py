"""Simulated industrial CO2 sensor stream with occasional anomaly spikes."""

import random
from datetime import datetime, timezone

from schemas.reading import EmissionReading

BASELINES_KG_PER_HOUR = {
    "Riverside Steel Plant": 120.0,
    "Northgate Cement Works": 200.0,
    "Harbor Power Station": 320.0,
}
SPIKE_PROBABILITY = 0.05
SPIKE_MULTIPLIER_RANGE = (2.5, 4.0)


def _reading_value(baseline: float) -> float:
    value = baseline + random.gauss(0, baseline * 0.05)
    if random.random() < SPIKE_PROBABILITY:
        value *= random.uniform(*SPIKE_MULTIPLIER_RANGE)
    return round(max(value, 0.0), 2)


def generate_readings(now: datetime | None = None) -> list[EmissionReading]:
    timestamp = now or datetime.now(timezone.utc)
    return [
        EmissionReading(
            timestamp=timestamp,
            source="sensor",
            metric="co2_kg_per_hour",
            value=_reading_value(baseline),
            unit="kg/h",
            facility_name=name,
        )
        for name, baseline in BASELINES_KG_PER_HOUR.items()
    ]
