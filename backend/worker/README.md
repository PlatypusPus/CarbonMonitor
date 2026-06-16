# worker/

APScheduler-based poller. Every `POLL_INTERVAL_MINUTES` (default 5) it calls the
external APIs (Electricity Maps, Carbon Interface, OpenWeatherMap) and the
internal sensor data generator, then ships readings to Logstash -> Elasticsearch.

Runs on a schedule (NOT per HTTP request) to stay within API rate limits.
Added in the API poller phase.
