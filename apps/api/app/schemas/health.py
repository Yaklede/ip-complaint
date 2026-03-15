from __future__ import annotations

from app.schemas.base import CamelModel


class DependencyHealth(CamelModel):
    status: str
    detail: str | None = None


class HealthResponse(CamelModel):
    status: str
    service: str
    version: str
    dependencies: dict[str, DependencyHealth]
