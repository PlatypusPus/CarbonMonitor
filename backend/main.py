"""CarbonTrace backend entrypoint."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from database import init_db
from routers import auth, emissions
from services.es import ensure_index_template

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    try:
        ensure_index_template()
    except Exception:
        logger.exception("Could not ensure Elasticsearch index template; continuing")
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

    # allow_credentials lets the browser send the refresh-token cookie cross-origin.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(emissions.router, prefix="/api/emissions", tags=["emissions"])

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok", "environment": settings.environment}

    return app


app = create_app()
