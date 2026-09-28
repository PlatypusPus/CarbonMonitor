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

## Active presentation instance

Use Docker at http://localhost. Its persistent PostgreSQL database contains the original 14 monthly electricity records under College Campus. The earlier local test servers and database on ports 5173 and 55439 are stopped. Do not start them for the presentation.

From the repository root:

```sh
docker compose up -d --build
docker compose restart nginx
docker compose ps
```

Restarting nginx after recreating backend or frontend containers refreshes its upstream addresses. Use the login supplied in the project chat; passwords are not committed. Do not run `docker compose down -v`, which deletes the persistent database volume.
