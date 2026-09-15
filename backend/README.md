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

OCR drafts are created with `POST /api/activity/ocr` and confirmed with
`POST /api/activity/ocr/{draft_id}/confirm`.

The frontend exposes the same flow on the **OCR Intake** page, and PDFs are supported
alongside image and text uploads.

## Lint

```bash
uv run ruff check .
```
