"""API entrypoint for the MechSense backend."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "Industrial machine-health monitoring API. "
        "Decision-support prototype — not certified condition-monitoring equipment."
    ),
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
register_exception_handlers(app)


@app.get("/health", tags=["health"], summary="Process health check")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "mechsense-api"}
