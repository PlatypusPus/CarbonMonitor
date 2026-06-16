# services/

Business logic kept out of the routers so it can be reused and tested:

- **es_client** — Elasticsearch connection + emission/anomaly queries.
- **anomaly_engine** — scikit-learn Isolation Forest training + scoring.
- **pdf_report** — ReportLab ESG report generation.

Added incrementally in their respective phases.
