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

from sqlalchemy.orm import Session

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


def run_detection(db: Session) -> int:
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import select
    from models.calculated_emission import CalculatedEmission
    from models.activity_record import ActivityRecord
    from models.facility import Facility
    from models.anomaly import Anomaly

    cutoff = datetime.now(timezone.utc) - timedelta(days=TRAIN_WINDOW_DAYS)
    
    stmt = (
        select(CalculatedEmission, ActivityRecord, Facility)
        .join(ActivityRecord, CalculatedEmission.activity_record_id == ActivityRecord.id)
        .join(Facility, ActivityRecord.facility_id == Facility.id)
        .where(CalculatedEmission.calculated_at >= cutoff)
    )
    
    results = db.execute(stmt).all()
    
    if not results:
        return 0
        
    readings = []
    for calc, record, fac in results:
        readings.append({
            "metric": record.activity_type,
            "facility_name": fac.name,
            "value": float(calc.co2e_kg),
            "unit": "kg CO2e",
            "source": record.source,
            "region": fac.region_code,
            "calculated_emission_id": calc.id,
            "timestamp": record.period_end
        })
        
    anomalies = detect(readings)
    
    count = 0
    for anomaly_data in anomalies:
        if anomaly_data.get("is_anomaly"):
            existing = db.execute(
                select(Anomaly).where(
                    Anomaly.calculated_emission_id == anomaly_data["calculated_emission_id"]
                )
            ).scalars().first()
            if not existing:
                db_anomaly = Anomaly(
                    timestamp=anomaly_data["timestamp"],
                    metric=anomaly_data["metric"],
                    facility_name=anomaly_data["facility_name"],
                    value=anomaly_data["value"],
                    unit=anomaly_data["unit"],
                    expected_value=anomaly_data["expected_value"],
                    anomaly_score=anomaly_data["anomaly_score"],
                    source=anomaly_data["source"],
                    region=anomaly_data["region"],
                    calculated_emission_id=anomaly_data["calculated_emission_id"]
                )
                db.add(db_anomaly)
                count += 1
            
    db.commit()
    return count


def query_anomalies(
    db: Session,
    metric: str | None = None,
    facility: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    from sqlalchemy import select
    from models.anomaly import Anomaly
    
    stmt = select(Anomaly).order_by(Anomaly.timestamp.desc()).limit(limit)
    if metric:
        stmt = stmt.where(Anomaly.metric == metric)
    if facility:
        stmt = stmt.where(Anomaly.facility_name == facility)
        
    db_anomalies = db.execute(stmt).scalars().all()
    
    return [
        {
            "timestamp": a.timestamp,
            "metric": a.metric,
            "facility_name": a.facility_name,
            "value": a.value,
            "unit": a.unit,
            "expected_value": a.expected_value,
            "anomaly_score": a.anomaly_score,
            "source": a.source,
            "region": a.region
        }
        for a in db_anomalies
    ]
