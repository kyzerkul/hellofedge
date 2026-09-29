"""Application FastAPI. Lancement : `uvicorn hellofedge.api.app:app`."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from hellofedge.api import feed
from hellofedge.config import get_settings
from hellofedge.db import make_engine
from hellofedge.logs import setup_logging

log = logging.getLogger("hellofedge.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    setup_logging(settings.log_level)
    app.state.engine = make_engine(settings.database_url)
    log.info("api démarrée")
    yield
    await app.state.engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Hellofedge",
        lifespan=lifespan,
        # Documentation de l'API fermée par défaut : l'api est en ligne sur le domaine
        # du trader. `API_DOCS=true` la rouvre, pour le développement local.
        docs_url="/api/docs" if settings.api_docs else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if settings.api_docs else None,
    )

    @app.get("/api/health")
    async def health(request: Request) -> JSONResponse:
        """Santé de l'api et de sa connexion à la base. 503 si la base ne répond pas."""
        try:
            async with request.app.state.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception:
            log.exception("base injoignable")
            return JSONResponse(
                {"status": "error", "database": "down"}, status_code=503
            )
        return JSONResponse({"status": "ok", "database": "ok"})

    app.include_router(feed.router)

    # Le cockpit construit est servi en dernier, pour ne jamais masquer une route /api.
    if settings.frontend_dist.is_dir():
        app.mount(
            "/",
            StaticFiles(directory=settings.frontend_dist, html=True),
            name="cockpit",
        )

    return app


app = create_app()
