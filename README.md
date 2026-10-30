# CarbonTrace

Review electricity and fuel records, calculate Scope 1 and Scope 2 emissions, and export a PDF report.

## Start

From the repository root:

```sh
docker compose up -d backend postgres
cd frontend
npm ci
npm run dev
```

Open **http://localhost:5173**. This is the active frontend. Docker supplies the API and persistent database; port 80 is disabled by default.

For a fresh installation, copy `.env.example` to `.env` first. See [setup and login](docs/setup.md).

## Use

Select a facility in Data Intake, upload and review records, then confirm them. Overview, Trends, and the PDF report use confirmed data.

## Repository layout

```
backend/     FastAPI API: routers, services, models, schemas, tests
frontend/    React + Vite app: pages, components, API hooks
nginx/       Reverse proxy for the optional packaged frontend
docs/        Setup, access, reporting and architecture guides
docs/report/ Project report (PDF) and features brief
scripts/     check.ps1 runs lint, tests and the build on Windows
```

## Documentation

- [Setup and login](docs/setup.md)
- [Facilities and user access](docs/access.md)
- [College dataset](docs/demo.md)
- [Calculations and reporting](docs/reporting.md)
- [Architecture and verification](docs/development.md)
- [Project report](docs/report/Report.pdf) and [features brief](docs/report/REPORT_FEATURES.md)

Built with React, FastAPI, and PostgreSQL. Seeded emission factors are demonstration placeholders.
