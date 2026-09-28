# CarbonTrace

A project demo for reviewing electricity and fuel records, calculating Scope 1 and Scope 2 emissions, comparing facilities, and exporting a PDF report.

## Start

Copy `.env.example` to `.env`, configure the database and JWT secret, then run:

```sh
docker compose up --build
```

Open http://localhost. Create your first account using [Setup and login](docs/setup.md).

## Use

1. Create a facility in Data Intake.
2. Choose files and assign each to its intended facility.
3. Check the preview, upload, and confirm the staged rows.
4. View Overview or Trends, then download the ESG report.

## Documentation

- [Setup, login, and local development](docs/setup.md)
- [Three-facility demo and spreadsheet imports](docs/demo.md)
- [Calculations, reporting, and limitations](docs/reporting.md)
- [Architecture and verification](docs/development.md)

Built with React, FastAPI, PostgreSQL, and Docker Compose. Seeded emission factors are placeholders for demonstration.
