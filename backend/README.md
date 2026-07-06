# CarbonTrace Backend

FastAPI service: auth, emissions API, anomaly detection, ESG PDF reports.

## Setup

```bash
uv sync                          # create .venv and install deps
cp ../.env.example ../.env       # fill in DATABASE_URL and JWT_SECRET_KEY
uv run uvicorn main:app --reload
```

Swagger UI: http://localhost:8000/docs  
Health check: http://localhost:8000/health

## Layout

```
routers/    HTTP endpoints (auth, facilities, activity, calculations,
            emissions, anomalies, recommendations, scenarios, reports, upload)
models/     SQLAlchemy models (Postgres)
schemas/    Pydantic request/response models
services/   calculation engine, OCR pipeline, anomaly detection,
            recommendation rules, scenario simulator, PDF generation
```

## Lint

```bash
uv run ruff check .
```
