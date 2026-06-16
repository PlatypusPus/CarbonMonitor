# CarbonTrace

Automated Carbon Emission Monitoring & ESG Reporting System.

CarbonTrace pulls carbon/emission data from external APIs (and a simulated
sensor generator), ingests it through the ELK stack, detects anomalies with an
Isolation Forest model, and presents everything on a React dashboard with
exportable ESG PDF reports.

## Architecture (high level)

```
External APIs + sensor generator
        │  (APScheduler poller, every 5 min)
        ▼
     Logstash ──► Elasticsearch ──► FastAPI ──► React dashboard
                       ▲                 │
                       └── anomaly engine (Isolation Forest)
   PostgreSQL ◄── users / auth / facilities / uploads
        Nginx = single reverse proxy in front of it all
```

## Tech stack
- **Frontend:** React + Vite, TailwindCSS, Recharts, React Query, Axios
- **Backend:** FastAPI, Python 3.11 (managed with **uv**), Uvicorn, SQLAlchemy, APScheduler
- **Data stores:** PostgreSQL (relational) + Elasticsearch (time-series)
- **Pipeline:** Logstash → Elasticsearch, visualised in Kibana
- **ML:** scikit-learn Isolation Forest
- **Reports:** ReportLab (PDF)
- **Infra:** Docker Compose, Nginx, deployed on GCP e2-medium

## Getting started
```bash
cp .env.example .env        # then fill in real values
docker compose up --build
```
- App (via nginx):  http://localhost
- API docs:         http://localhost/api/docs  (once routers are mounted)
- Kibana:           http://localhost:5601

## Build phases
1. **Infrastructure** — Docker Compose, env, scaffold  ← *current*
2. Backend scaffold & settings
3. Auth (JWT + refresh cookie, roles)
4. Database models (Postgres)
5. API poller (APScheduler + external APIs)
6. Logstash pipeline → Elasticsearch
7. FastAPI endpoints (emissions, uploads)
8. Anomaly engine (Isolation Forest)
9. Frontend pages
