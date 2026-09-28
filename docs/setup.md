# Setup and login

## Docker

Copy `.env.example` to `.env`, fill in the environment values, and run `docker compose up --build` from the repository root. The app is at http://localhost and API documentation is at http://localhost/api/docs.

There is no default login and no public sign-up. Create an administrator:

```sh
docker compose exec backend python create_admin.py --email you@example.com --password "your-chosen-password" --role admin
```

Use that email and password on the login page. Running this command for an existing email leaves its password unchanged. Test-suite credentials belong only to the disposable test database.

## Local development

Requirements: PostgreSQL, Python 3.11 or later with uv, Node 20 or later with npm.

1. Copy `.env.example` to `.env`. Set `DATABASE_URL` to your local PostgreSQL address. The hostname `postgres` works inside Docker only; use `127.0.0.1` locally.
2. From `backend`, run `uv sync --frozen`, then `uv run python create_admin.py --email you@example.com --password "your-chosen-password"`.
3. Start the API with `uv run uvicorn main:app --reload`.
4. From `frontend`, run `npm ci` and `npm run dev`.
5. Open http://localhost:5173. Vite proxies `/api` to port 8000.

Restart the service after changing environment variables. Rebuild Docker images after code changes with `docker compose up --build`.

## Prepared local presentation database

The prepared demo uses database `carbontrace_demo` on `127.0.0.1:55439`, separate from Docker and the disposable `_e2e` database. It contains 14 confirmed records across Demo Facility 1, 2, and 3. Login credentials were supplied in the project chat and are not committed.

If the local services have stopped, run from the repository root in PowerShell:

```powershell
& 'C:/Program Files/PostgreSQL/18/bin/pg_ctl.exe' -D '.test-postgres' -l 'demo-postgres.log' -o '-h 127.0.0.1 -p 55439' start
$env:DATABASE_URL = 'postgresql+psycopg://carbontrace@127.0.0.1:55439/carbontrace_demo?connect_timeout=3'
$env:ENVIRONMENT = 'development'
cd backend
uv run uvicorn main:app --host 127.0.0.1 --port 8000
```

In a second terminal, run `cd frontend` and `npm run dev -- --host localhost --port 5173 --strictPort`. Open http://localhost:5173. The Vite proxy explicitly targets IPv4 to avoid reaching a different API listening on IPv6 localhost. If port 8000 is already occupied on IPv4, stop the earlier local API before starting another.

The local PostgreSQL cluster uses trusted loopback access for development. Keep it local, retain `.test-postgres` to preserve the demo data, and use the Docker setup for a separately configured deployment.
