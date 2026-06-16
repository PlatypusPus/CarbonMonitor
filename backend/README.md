# CarbonTrace Backend

FastAPI service: auth, emissions API, anomaly engine, ESG PDF reports, and the
APScheduler worker that polls external carbon APIs.

## Local development (with uv)

```bash
cd backend
uv sync                 # create .venv and install all deps (incl. dev tools)
uv run uvicorn main:app --reload
```

Then open http://localhost:8000/health and http://localhost:8000/docs.

## Layout
- `routers/`  — API endpoints (auth, emissions, anomalies, reports, upload)
- `models/`   — SQLAlchemy models (User, Facility, Upload)
- `services/` — ES queries, anomaly engine, PDF generation
- `worker/`   — APScheduler poller for the external APIs
