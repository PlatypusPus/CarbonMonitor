"""CarbonTrace backend entrypoint.

This is intentionally minimal for Phase 0 — it only proves the app boots and
exposes a health check. Routers, database, auth, the poller, and the anomaly
engine are wired in during later phases.
"""

from fastapi import FastAPI

app = FastAPI(
    title="CarbonTrace API",
    version="0.1.0",
    description="Automated carbon emission monitoring & ESG reporting.",
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Liveness probe used by Docker/nginx to confirm the API is up."""
    return {"status": "ok"}


# Routers are included here in later phases, e.g.:
# from routers import auth, emissions, anomalies, reports, upload
# app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
