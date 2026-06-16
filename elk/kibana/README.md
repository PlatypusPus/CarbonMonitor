# elk/kibana/

Kibana is configured via the `kibana` service in docker-compose.yml and reaches
Elasticsearch at http://elasticsearch:9200.

Exported saved objects (index patterns, dashboards) can be committed here later
as NDJSON so the Kibana setup is reproducible.
