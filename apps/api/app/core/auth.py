from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Depends, Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import Settings, get_settings
from app.core.errors import ApiException


@dataclass(slots=True)
class RequestPrincipal:
    actor: str
    roles: set[str]


class RBACStubMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings: Settings) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self._settings = settings

    async def dispatch(self, request, call_next):  # type: ignore[no-untyped-def]
        actor = request.headers.get("x-actor", self._settings.auth_default_actor)
        roles_header = request.headers.get(
            "x-roles", ",".join(self._settings.auth_default_role_list)
        )
        roles = {item.strip() for item in roles_header.split(",") if item.strip()}
        request.state.principal = RequestPrincipal(actor=actor, roles=roles)
        return await call_next(request)


def get_principal(request: Request) -> RequestPrincipal:
    principal = getattr(request.state, "principal", None)
    if principal is None:
        settings = get_settings()
        return RequestPrincipal(
            actor=settings.auth_default_actor,
            roles=set(settings.auth_default_role_list),
        )
    return principal


def require_roles(*required_roles: str) -> Callable[[RequestPrincipal], RequestPrincipal]:
    def dependency(principal: RequestPrincipal = Depends(get_principal)) -> RequestPrincipal:
        if not required_roles:
            return principal
        if principal.roles.intersection(required_roles):
            return principal
        raise ApiException(
            status_code=403,
            code="FORBIDDEN",
            message="Missing required role for this action",
            details={"requiredRoles": list(required_roles)},
        )

    return dependency
