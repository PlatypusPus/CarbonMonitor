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

## Documentation

- [Setup and login](docs/setup.md)
- [Facilities and user access](docs/access.md)
- [College dataset](docs/demo.md)
- [Calculations and reporting](docs/reporting.md)
- [Architecture and verification](docs/development.md)

Built with React, FastAPI, and PostgreSQL. Seeded emission factors are demonstration placeholders.
