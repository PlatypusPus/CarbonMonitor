"""Elasticsearch queries for emission readings."""

from typing import Any

from elasticsearch import NotFoundError

from services.es import get_es_client

LIVE_INDEX = "emissions-live"


def _to_record(source: dict[str, Any]) -> dict[str, Any]:
    record = dict(source)
    record["timestamp"] = record.pop("@timestamp", record.get("timestamp"))
    return record


def query_latest(
    metric: str | None = None,
    source: str | None = None,
    facility: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    filters: list[dict[str, Any]] = []
    if metric:
        filters.append({"term": {"metric": metric}})
    if source:
        filters.append({"term": {"source": source}})
    if facility:
        filters.append({"term": {"facility_name": facility}})
    query = {"bool": {"filter": filters}} if filters else {"match_all": {}}
    try:
        response = get_es_client().search(
            index=LIVE_INDEX,
            query=query,
            sort=[{"@timestamp": {"order": "desc"}}],
            size=limit,
        )
    except NotFoundError:
        return []
    return [_to_record(hit["_source"]) for hit in response["hits"]["hits"]]


def query_timeseries(
    metric: str,
    interval: str = "1h",
    source: str | None = None,
) -> list[dict[str, Any]]:
    filters: list[dict[str, Any]] = [{"term": {"metric": metric}}]
    if source:
        filters.append({"term": {"source": source}})
    try:
        response = get_es_client().search(
            index=LIVE_INDEX,
            size=0,
            query={"bool": {"filter": filters}},
            aggs={
                "series": {
                    "date_histogram": {"field": "@timestamp", "fixed_interval": interval},
                    "aggs": {"avg_value": {"avg": {"field": "value"}}},
                }
            },
        )
    except NotFoundError:
        return []
    buckets = response["aggregations"]["series"]["buckets"]
    return [
        {"timestamp": b["key_as_string"], "value": b["avg_value"]["value"], "count": b["doc_count"]}
        for b in buckets
    ]


def query_summary() -> list[dict[str, Any]]:
    try:
        response = get_es_client().search(
            index=LIVE_INDEX,
            size=0,
            aggs={
                "metrics": {
                    "terms": {"field": "metric", "size": 50},
                    "aggs": {
                        "avg_value": {"avg": {"field": "value"}},
                        "latest": {
                            "top_hits": {"size": 1, "sort": [{"@timestamp": {"order": "desc"}}]}
                        },
                    },
                }
            },
        )
    except NotFoundError:
        return []
    summaries = []
    for bucket in response["aggregations"]["metrics"]["buckets"]:
        latest = bucket["latest"]["hits"]["hits"][0]["_source"]
        summaries.append(
            {
                "metric": bucket["key"],
                "count": bucket["doc_count"],
                "avg_value": bucket["avg_value"]["value"],
                "latest_value": latest.get("value"),
                "unit": latest.get("unit"),
                "latest_timestamp": latest.get("@timestamp") or latest.get("timestamp"),
            }
        )
    return summaries
