import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.routing import APIRoute

from app.config import get_settings
from app.errors import register_error_handlers
from app.routers import health

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

API_PREFIX = "/api/v1"


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Lead Tracker API",
        version="1.0.0",
        summary="Create, list, search and update the status of sales leads.",
        openapi_tags=[
            {"name": "health", "description": "Liveness and database connectivity."},
        ],
        docs_url="/docs",
        redoc_url="/redoc",
        generate_unique_id_function=lambda route: route.name if isinstance(route, APIRoute) else "",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Content-Type"],
        allow_credentials=False,
    )
    register_error_handlers(app)
    app.include_router(health.router, prefix=API_PREFIX)

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse("/docs")

    return app


app = create_app()
