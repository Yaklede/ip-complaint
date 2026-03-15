from __future__ import annotations

import socket
from urllib.parse import urlparse

from fastapi import APIRouter, Request
from sqlalchemy import text

from app.schemas.health import DependencyHealth, HealthResponse


router = APIRouter()


def _check_endpoint(endpoint: str) -> DependencyHealth:
    if not endpoint:
        return DependencyHealth(status="not_configured", detail="No endpoint configured")

    parsed = urlparse(endpoint)
    host = parsed.hostname
    port = parsed.port
    if host is None:
        return DependencyHealth(status="unknown", detail="Could not parse endpoint")

    if port is None:
        port = 443 if parsed.scheme == "https" else 80

    try:
        with socket.create_connection((host, port), timeout=0.5):
            return DependencyHealth(status="ready")
    except OSError as exc:
        return DependencyHealth(status="unreachable", detail=str(exc))


@router.get("/healthz", response_model=HealthResponse)
def healthz(request: Request) -> HealthResponse:
    db_status = DependencyHealth(status="ready")
    try:
        with request.app.state.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - exercised through health test failure cases
        db_status = DependencyHealth(status="unreachable", detail=str(exc))

    settings = request.app.state.settings
    dependencies = {
        "database": db_status,
        "opensearch": _check_endpoint(settings.opensearch_url),
        "minio": _check_endpoint(settings.minio_endpoint),
        "redis": _check_endpoint(settings.redis_url),
    }
    overall = "ok" if dependencies["database"].status == "ready" else "degraded"
    return HealthResponse(
        status=overall,
        service=settings.app_name,
        version=settings.api_version,
        dependencies=dependencies,
    )
