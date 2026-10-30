"""12-month emissions forecast from confirmed history, with optional ongoing changes."""
from collections import defaultdict

from schemas.scenario import ForecastMonth


def index(key):
    return key[0] * 12 + key[1] - 1


def forecast(rows, future_changes=(), months=12) -> list[ForecastMonth]:
    """rows: (activity_type, period_start, co2e_kg) for confirmed records.

    ponytail: seasonal-naive (same month last year, else mean of the last 3 months);
    swap for a fitted model if forecasts need trend or confidence bands.
    """
    series = defaultdict(lambda: defaultdict(float))
    for activity, start, kg in rows:
        series[activity][(start.year, start.month)] += kg
    if not series:
        return []
    last = max(key for months_kg in series.values() for key in months_kg)
    # Activities with no data in the past year are treated as stopped.
    active = {a: s for a, s in series.items() if index(last) - index(max(s)) < 12}
    result, (year, month) = [], last
    for _ in range(months):
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
        label = f"{year:04d}-{month:02d}"
        baseline = projected = 0.0
        for activity, history in active.items():
            value = history.get((year - 1, month))
            if value is None:
                recent = [history[k] for k in sorted(history)[-3:]]
                value = sum(recent) / len(recent)
            factor = 1.0
            for change in future_changes:
                if change.activity_type == activity and (change.start_month or "") <= label:
                    factor *= 1 + change.change_percent / 100
            baseline += value
            projected += value * max(factor, 0)
        result.append(ForecastMonth(month=label, baseline_co2e_kg=baseline, projected_co2e_kg=projected))
    return result

