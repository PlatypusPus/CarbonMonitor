# Setup and login

## Active setup: frontend on port 5173

Run these commands from the repository root:

```sh
docker compose up -d backend postgres
cd frontend
npm ci
npm run dev
```

Open **http://localhost:5173**. Vite proxies `/api` to Docker's API on `127.0.0.1:8000`. Port 5173 is fixed; if another dev server is already using it, Vite stops instead of silently opening a different port. Use the running instance or stop it before restarting.

Docker's persistent database contains 14 original college electricity records under College Campus. The former local test database on port 55439 is stopped. Passwords are supplied in the project chat, not committed.

## Fresh installation and accounts

Copy `.env.example` to `.env` and configure its secrets before starting Docker. Create an administrator from the repository root:

```sh
docker compose exec backend python create_admin.py --email you@example.com --password "your-chosen-password" --role admin
```

An existing email keeps its password. There is no public sign-up or default account.

## Updates and stopping

After backend changes, run `docker compose up -d --build backend`. Vite automatically refreshes frontend changes. Stop Vite with Ctrl+C in its terminal. `docker compose stop` stops Docker services without deleting data. Never use `docker compose down -v` unless you intend to delete the database.

## Optional packaged frontend

Docker's static frontend and port-80 proxy are disabled by default behind the `web` profile. They are not needed for the presentation. Only start them intentionally with `docker compose --profile web up -d --build`. Stop them with `docker compose --profile web stop frontend nginx` before returning to the single frontend on port 5173.
