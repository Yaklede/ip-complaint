from __future__ import annotations

from fastapi import APIRouter

from app.api.routers import cases, events, health


api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(events.router, prefix="/v1")
api_router.include_router(cases.router, prefix="/v1")
