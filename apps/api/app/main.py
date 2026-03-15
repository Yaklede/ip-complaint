from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.auth import RBACStubMiddleware
from app.core.config import Settings, get_settings
from app.core.errors import ApiException, api_exception_handler
from app.db.session import create_db_engine, create_session_factory


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    engine = create_db_engine(resolved_settings.database_url)
    session_factory = create_session_factory(engine)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.settings = resolved_settings
        app.state.engine = engine
        app.state.session_factory = session_factory
        yield
        engine.dispose()

    app = FastAPI(
        title=resolved_settings.app_name,
        version=resolved_settings.api_version,
        lifespan=lifespan,
    )
    app.add_exception_handler(ApiException, api_exception_handler)
    app.add_middleware(RBACStubMiddleware, settings=resolved_settings)
    app.include_router(api_router)
    return app


app = create_app()
