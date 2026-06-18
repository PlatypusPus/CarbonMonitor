"""Elasticsearch client and index-template bootstrap."""

import logging

from elasticsearch import Elasticsearch

from config import get_settings

logger = logging.getLogger(__name__)

INDEX_TEMPLATE_NAME = "emissions"
INDEX_PATTERNS = ["emissions-*"]

_INDEX_SETTINGS = {
    "number_of_shards": 1,
    "number_of_replicas": 0,
}
_MAPPINGS = {
    "properties": {
        "@timestamp": {"type": "date"},
        "timestamp": {"type": "date"},
        "source": {"type": "keyword"},
        "metric": {"type": "keyword"},
        "value": {"type": "double"},
        "unit": {"type": "keyword"},
        "facility_id": {"type": "keyword"},
        "facility_name": {"type": "keyword"},
        "region": {"type": "keyword"},
        "upload_id": {"type": "keyword"},
        "is_anomaly": {"type": "boolean"},
        "anomaly_score": {"type": "double"},
        "expected_value": {"type": "double"},
    }
}

_client: Elasticsearch | None = None


def get_es_client() -> Elasticsearch:
    global _client
    if _client is None:
        _client = Elasticsearch(get_settings().elasticsearch_url)
    return _client


def ensure_index_template() -> None:
    get_es_client().indices.put_index_template(
        name=INDEX_TEMPLATE_NAME,
        index_patterns=INDEX_PATTERNS,
        template={"settings": _INDEX_SETTINGS, "mappings": _MAPPINGS},
        priority=200,
    )
    logger.info("Ensured Elasticsearch index template '%s'", INDEX_TEMPLATE_NAME)
