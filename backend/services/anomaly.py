"""Isolation Forest anomaly detection over emission readings."""

import logging
from collections import defaultdict
from typing import Any

import numpy as np
from elasticsearch import ConnectionError as ESConnectionError
from elasticsearch import NotFoundError
from elasticsearch.helpers import bulk, scan
from sklearn.ensemble import IsolationForest

from services.emissions import LIVE_INDEX
from services.es import get_es_client

logger = logging.getLogger(__name__)

MIN_SAMPLES = 20
RANDOM_STATE = 42
CONTAMINATION = 0.06
ANOMALY_INDEX = "emissions-anomalies"
TRAIN_WINDOW = "now-7d"


def detect(
    readings: list[dict[str, Any]],
    min_samples: int = MIN_SAMPLES,
    contamination: float | str = CONTAMINATION,
) -> list[dict[str, Any]]:
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


def _fetch_recent(index: str, window: str = TRAIN_WINDOW) -> list[dict[str, Any]]:
    body = {"query": {"range": {"@timestamp": {"gte": window}}}}
    readings: list[dict[str, Any]] = []
    for hit in scan(get_es_client(), index=index, query=body, preserve_order=False):
        source = dict(hit["_source"])
        source["doc_id"] = hit["_id"]
        readings.append(source)
    return readings


def run_detection(live_index: str = LIVE_INDEX, anomaly_index: str = ANOMALY_INDEX) -> int:
    try:
        readings = _fetch_recent(live_index)
    except NotFoundError:
        return 0
    except ESConnectionError:
        logger.warning("Anomaly detection skipped: Elasticsearch unavailable")
        return 0

    anomalies = detect(readings)
    if not anomalies:
        return 0

    actions = []
    for anomaly in anomalies:
        record = dict(anomaly)
        doc_id = record.pop("doc_id", None)
        action: dict[str, Any] = {"_index": anomaly_index, "_source": record}
        if doc_id is not None:
            action["_id"] = doc_id
        actions.append(action)
    success, _ = bulk(get_es_client(), actions)
    logger.info("Indexed %d anomaly record(s)", success)
    return success


def query_anomalies(
    metric: str | None = None,
    facility: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    filters: list[dict[str, Any]] = []
    if metric:
        filters.append({"term": {"metric": metric}})
    if facility:
        filters.append({"term": {"facility_name": facility}})
    query = {"bool": {"filter": filters}} if filters else {"match_all": {}}
    try:
        response = get_es_client().search(
            index=ANOMALY_INDEX,
            query=query,
            sort=[{"@timestamp": {"order": "desc"}}],
            size=limit,
        )
    except NotFoundError:
        return []
    records = []
    for hit in response["hits"]["hits"]:
        source = dict(hit["_source"])
        source["timestamp"] = source.pop("@timestamp", source.get("timestamp"))
        records.append(source)
    return records
