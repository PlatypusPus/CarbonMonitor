"""CarbonTrace backend entrypoint."""

import logging
from contextlib import asynccontextmanager

from elasticsearch import ConnectionError as ESConnectionError
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings
from database import init_db
from routers import anomalies, auth, emissions, reports, upload
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

    @app.exception_handler(ESConnectionError)
    async def _es_unavailable(request: Request, exc: ESConnectionError) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": "Elasticsearch unavailable"})

    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(emissions.router, prefix="/api/emissions", tags=["emissions"])
    app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
    app.include_router(anomalies.router, prefix="/api/anomalies", tags=["anomalies"])
    app.include_router(reports.router, prefix="/api/reports", tags=["reports"])

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok", "environment": settings.environment}

    return app


app = create_app()
