"""CarbonTrace backend entrypoint."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from database import init_db
from routers import anomalies, auth, emissions, reports, upload
from routers import activity, calculations, facilities, recommendations, scenarios

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    settings.assert_production_ready()

    app = FastAPI(
        title="CarbonTrace API",
        version="0.1.0",
        description="Automated carbon emission monitoring & ESG reporting.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(emissions.router, prefix="/api/emissions", tags=["emissions"])
    app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
    app.include_router(anomalies.router, prefix="/api/anomalies", tags=["anomalies"])
    app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
    app.include_router(facilities.router, prefix="/api/facilities", tags=["facilities"])
    app.include_router(activity.router, prefix="/api/activity", tags=["activity"])
    app.include_router(calculations.router, prefix="/api/calculations", tags=["calculations"])
    app.include_router(recommendations.router, prefix="/api/recommendations", tags=["recommendations"])
    app.include_router(scenarios.router, prefix="/api/scenarios", tags=["scenarios"])

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok", "environment": settings.environment}

    return app


app = create_app()
