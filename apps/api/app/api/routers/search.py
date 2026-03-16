from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import RequestPrincipal, require_roles
from app.db.session import get_db_session
from app.schemas.search import CorrelateRequest, CorrelateResponse
from app.services.search import CorrelationService


router = APIRouter(tags=["search"])


@router.post("/search/correlate", response_model=CorrelateResponse)
def correlate(
    payload: CorrelateRequest,
    session: Session = Depends(get_db_session),
    _: RequestPrincipal = Depends(
        require_roles(
            "investigator",
            "lead",
            "admin",
            "auditor",
            "legal_reviewer",
            "privacy_reviewer",
        )
    ),
) -> CorrelateResponse:
    return CorrelationService(session).correlate(payload)
