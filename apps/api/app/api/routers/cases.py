from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.auth import RequestPrincipal, require_roles
from app.db.session import get_db_session
from app.schemas.cases import (
    CaseDetailResponse,
    CaseListResponse,
    CaseResponse,
    CreateCaseRequest,
    FreezeResponse,
)
from app.services.cases import CaseService
from app.services.evidence import EvidenceService


router = APIRouter(tags=["cases"])


@router.get("/cases", response_model=CaseListResponse)
def list_cases(
    status_filter: str | None = Query(default=None, alias="status"),
    severity: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, alias="pageSize", ge=1, le=100),
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
) -> CaseListResponse:
    return CaseService(session).list_cases(
        status=status_filter, severity=severity, page=page, page_size=page_size
    )


@router.post("/cases", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(
    payload: CreateCaseRequest,
    session: Session = Depends(get_db_session),
    principal: RequestPrincipal = Depends(require_roles("investigator", "lead", "admin")),
) -> CaseResponse:
    return CaseService(session).create_case(payload, principal)


@router.get("/cases/{case_id}", response_model=CaseDetailResponse)
def get_case(
    case_id: UUID,
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
) -> CaseDetailResponse:
    return CaseService(session).get_case(case_id)


@router.post(
    "/cases/{case_id}/freeze",
    response_model=FreezeResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def freeze_case(
    case_id: UUID,
    session: Session = Depends(get_db_session),
    principal: RequestPrincipal = Depends(require_roles("investigator", "lead", "admin")),
) -> FreezeResponse:
    return EvidenceService(session).freeze_case(case_id, principal)
