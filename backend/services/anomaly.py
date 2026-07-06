"""Isolation Forest anomaly detection over emission readings.

The detect() function is pure and framework-independent — keep it that way.

TODO: _fetch_recent(), run_detection(), and query_anomalies() previously used Elasticsearch
(emissions-live / emissions-anomalies indices). ES has been removed. Migrate to:
  - _fetch_recent()    → query calculated_emissions from Postgres for the trailing window
  - run_detection()    → persist flagged results to an anomaly table in Postgres (not yet modelled)
  - query_anomalies()  → query that Postgres anomaly table
"""

import logging
from collections import defaultdict
from typing import Any

import numpy as np
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)

MIN_SAMPLES = 20
RANDOM_STATE = 42
CONTAMINATION = 0.06
TRAIN_WINDOW_DAYS = 7


def detect(
    readings: list[dict[str, Any]],
    min_samples: int = MIN_SAMPLES,
    contamination: float | str = CONTAMINATION,
) -> list[dict[str, Any]]:
    """Pure Isolation Forest over a list of reading dicts.

    Each reading must have 'value', 'metric', and 'facility_name' keys.
    Returns the subset flagged as anomalies, each extended with
    'is_anomaly', 'anomaly_score', and 'expected_value'.
    """
    groups: dict[tuple[Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for reading in readings:
        groups[(reading.get("metric"), reading.get("facility_name"))].append(reading)

    anomalies: list[dict[str, Any]] = []
    for items in groups.values():
        if len(items) < min_samples:
            continue
        values = np.array([[float(item["value"])] for item in items])
        model = IsolationForest(contamination=contamination, random_state=RANDOM_STATE)
        predictions = model.fit_predict(values)
        scores = model.score_samples(values)

        inliers = values[predictions == 1].ravel()
        expected = float(np.median(inliers if inliers.size else values))

        for item, prediction, score in zip(items, predictions, scores):
            if prediction == -1:
                anomalies.append(
                    {
                        **item,
                        "is_anomaly": True,
                        "anomaly_score": round(float(score), 4),
                        "expected_value": round(expected, 2),
                    }
                )
    return anomalies


def run_detection() -> int:
    # TODO: fetch calculated_emissions from Postgres for the trailing TRAIN_WINDOW_DAYS,
    # call detect(), persist flagged rows to a Postgres anomaly table (model not yet defined).
    # Return count of anomalies written.
    logger.warning("run_detection: not yet implemented — Postgres anomaly table pending")
    return 0


def query_anomalies(
    metric: str | None = None,
    facility: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    # TODO: query Postgres anomaly table once run_detection() is implemented.
    return []
