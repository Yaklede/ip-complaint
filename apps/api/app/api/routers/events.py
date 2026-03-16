from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.auth import RequestPrincipal, require_roles
from app.db.session import get_db_session
from app.schemas.events import IngestRequest, IngestResponse
from app.services.ingest import IngestService


router = APIRouter(tags=["ingest"])


@router.post("/events:ingest", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
def ingest_events(
    payload: IngestRequest,
    request: Request,
    session: Session = Depends(get_db_session),
    principal: RequestPrincipal = Depends(require_roles("investigator", "lead", "admin")),
) -> IngestResponse:
    return IngestService(
        session,
        request.app.state.raw_artifact_storage,
        request.app.state.parser_registry,
    ).ingest(payload, principal)
