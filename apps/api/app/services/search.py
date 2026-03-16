from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import ApiException
from app.core.policy import (
    EXTERNAL_UNKNOWN_DISPLAY_NAME,
    EXTERNAL_UNKNOWN_GRADE,
    EXTERNAL_UNKNOWN_NEXT_STEP,
    is_external_public_ip,
)
from app.models.entities import Asset, AssetNetworkBinding, Case, CaseEvent, NormalizedEvent, User
from app.models.enums import ActorType
from app.schemas.cases import CaseResponse
from app.schemas.events import NormalizedEventResponse
from app.schemas.search import (
    AttributionPreviewResponse,
    CandidateAssetResponse,
    CandidateUserResponse,
    CorrelateQueryType,
    CorrelateRequest,
    CorrelateResponse,
)

INTERNAL_PREVIEW_NEXT_STEP = "DHCP/VPN/AD/EDR/CMDB 교차검증 필요"


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@dataclass(slots=True)
class AssetCandidateAccumulator:
    asset: Asset
    observed_ips: set[str] = field(default_factory=set)
    matched_by: set[str] = field(default_factory=set)


@dataclass(slots=True)
class UserCandidateAccumulator:
    user: User
    matched_by: set[str] = field(default_factory=set)


class CorrelationService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def correlate(self, payload: CorrelateRequest) -> CorrelateResponse:
        payload = payload.model_copy(update={"query_value": payload.query_value.strip()})
        time_from = ensure_utc(payload.time_from)
        time_to = ensure_utc(payload.time_to)
        if time_from > time_to:
            raise ApiException(
                status_code=422,
                code="INVALID_TIME_RANGE",
                message="timeFrom must be earlier than or equal to timeTo",
            )

        related_events = self._load_related_events(payload.query_type, payload.query_value, time_from, time_to)
        related_cases = self._load_related_cases([event.id for event in related_events])
        user_candidates = self._collect_user_candidates(payload, related_events)
        asset_candidates = self._collect_asset_candidates(
            payload,
            related_events,
            user_candidates,
            time_from,
            time_to,
        )
        self._expand_user_candidates_from_assets(user_candidates, asset_candidates)

        candidate_asset_responses = self._serialize_asset_candidates(asset_candidates)
        candidate_user_responses = self._serialize_user_candidates(user_candidates)

        return CorrelateResponse(
            related_events=[NormalizedEventResponse.model_validate(event) for event in related_events],
            related_cases=[CaseResponse.model_validate(item) for item in related_cases],
            candidate_assets=candidate_asset_responses,
            candidate_users=candidate_user_responses,
            attribution_preview=self._build_attribution_preview(
                payload,
                candidate_user_responses,
            ),
        )

    def _load_related_events(
        self,
        query_type: CorrelateQueryType,
        query_value: str,
        time_from: datetime,
        time_to: datetime,
    ) -> list[NormalizedEvent]:
        statement = (
            select(NormalizedEvent)
            .where(NormalizedEvent.event_time >= time_from)
            .where(NormalizedEvent.event_time <= time_to)
            .options(selectinload(NormalizedEvent.source))
            .order_by(NormalizedEvent.event_time.desc())
        )

        normalized_value = query_value.strip()
        lowered_value = normalized_value.casefold()
        if query_type == CorrelateQueryType.IP:
            statement = statement.where(
                or_(
                    NormalizedEvent.src_ip == normalized_value,
                    NormalizedEvent.dst_ip == normalized_value,
                )
            )
        elif query_type == CorrelateQueryType.USERNAME:
            statement = statement.where(func.lower(NormalizedEvent.username) == lowered_value)
        elif query_type == CorrelateQueryType.HOSTNAME:
            statement = statement.where(func.lower(NormalizedEvent.hostname) == lowered_value)
        elif query_type == CorrelateQueryType.SESSION:
            statement = statement.where(func.lower(NormalizedEvent.session_id) == lowered_value)
        elif query_type == CorrelateQueryType.DOMAIN:
            statement = statement.where(func.lower(NormalizedEvent.request_host) == lowered_value)

        return self._session.scalars(statement).all()

    def _load_related_cases(self, event_ids: list[UUID]) -> list[Case]:
        if not event_ids:
            return []

        statement = (
            select(Case)
            .join(CaseEvent, CaseEvent.case_id == Case.id)
            .where(CaseEvent.event_id.in_(event_ids))
            .order_by(Case.opened_at.desc())
            .distinct()
        )
        return self._session.scalars(statement).unique().all()

    def _collect_user_candidates(
        self,
        payload: CorrelateRequest,
        related_events: list[NormalizedEvent],
    ) -> dict[UUID, UserCandidateAccumulator]:
        candidates: dict[UUID, UserCandidateAccumulator] = {}

        if payload.query_type == CorrelateQueryType.USERNAME:
            for user in self._load_users_by_usernames({payload.query_value}):
                self._merge_user_candidate(candidates, user, "directory_username")

        event_usernames = {event.username for event in related_events if event.username}
        for user in self._load_users_by_usernames(event_usernames):
            self._merge_user_candidate(candidates, user, "event_username")

        return candidates

    def _collect_asset_candidates(
        self,
        payload: CorrelateRequest,
        related_events: list[NormalizedEvent],
        user_candidates: dict[UUID, UserCandidateAccumulator],
        time_from: datetime,
        time_to: datetime,
    ) -> dict[UUID, AssetCandidateAccumulator]:
        candidates: dict[UUID, AssetCandidateAccumulator] = {}

        if payload.query_type == CorrelateQueryType.IP:
            for asset, observed_ip in self._load_assets_for_ip(payload.query_value, time_from, time_to):
                self._merge_asset_candidate(candidates, asset, "network_binding", observed_ip)

        direct_hostnames: set[str] = set()
        if payload.query_type == CorrelateQueryType.HOSTNAME:
            direct_hostnames.add(payload.query_value)
        event_hostnames = {event.hostname for event in related_events if event.hostname}
        direct_hostnames.update(event_hostnames)
        for asset in self._load_assets_by_hostnames(direct_hostnames):
            matched_by = "asset_hostname" if asset.hostname.casefold() == payload.query_value.casefold() else "event_hostname"
            self._merge_asset_candidate(candidates, asset, matched_by)

        if user_candidates:
            user_ids = set(user_candidates)
            for asset in self._load_assets_for_users(user_ids):
                self._merge_asset_candidate(candidates, asset, "user_assignment")

        return candidates

    def _expand_user_candidates_from_assets(
        self,
        user_candidates: dict[UUID, UserCandidateAccumulator],
        asset_candidates: dict[UUID, AssetCandidateAccumulator],
    ) -> None:
        for candidate in asset_candidates.values():
            if candidate.asset.primary_user is not None:
                self._merge_user_candidate(
                    user_candidates,
                    candidate.asset.primary_user,
                    "primary_asset_assignment",
                )
            if candidate.asset.owner_user is not None:
                self._merge_user_candidate(
                    user_candidates,
                    candidate.asset.owner_user,
                    "owner_asset_assignment",
                )

    def _load_users_by_usernames(self, usernames: set[str | None]) -> list[User]:
        normalized_usernames = {item.casefold() for item in usernames if item}
        if not normalized_usernames:
            return []

        statement = (
            select(User)
            .where(func.lower(User.username).in_(normalized_usernames))
            .order_by(User.display_name.asc())
        )
        return self._session.scalars(statement).all()

    def _load_assets_by_hostnames(self, hostnames: set[str | None]) -> list[Asset]:
        normalized_hostnames = {item.casefold() for item in hostnames if item}
        if not normalized_hostnames:
            return []

        statement = (
            select(Asset)
            .where(func.lower(Asset.hostname).in_(normalized_hostnames))
            .options(selectinload(Asset.owner_user), selectinload(Asset.primary_user))
            .order_by(Asset.hostname.asc())
        )
        return self._session.scalars(statement).unique().all()

    def _load_assets_for_users(self, user_ids: set[UUID]) -> list[Asset]:
        if not user_ids:
            return []

        statement = (
            select(Asset)
            .where(or_(Asset.owner_user_id.in_(user_ids), Asset.primary_user_id.in_(user_ids)))
            .options(selectinload(Asset.owner_user), selectinload(Asset.primary_user))
            .order_by(Asset.hostname.asc())
        )
        return self._session.scalars(statement).unique().all()

    def _load_assets_for_ip(
        self,
        query_value: str,
        time_from: datetime,
        time_to: datetime,
    ) -> list[tuple[Asset, str]]:
        statement = (
            select(Asset, AssetNetworkBinding.ip)
            .join(AssetNetworkBinding, AssetNetworkBinding.asset_id == Asset.id)
            .where(AssetNetworkBinding.ip == query_value)
            .where(AssetNetworkBinding.lease_start <= time_to)
            .where(AssetNetworkBinding.lease_end >= time_from)
            .options(selectinload(Asset.owner_user), selectinload(Asset.primary_user))
            .order_by(Asset.hostname.asc())
        )
        return [(asset, observed_ip) for asset, observed_ip in self._session.execute(statement).all()]

    def _merge_user_candidate(
        self,
        candidates: dict[UUID, UserCandidateAccumulator],
        user: User,
        matched_by: str,
    ) -> None:
        candidate = candidates.get(user.id)
        if candidate is None:
            candidate = UserCandidateAccumulator(user=user)
            candidates[user.id] = candidate
        candidate.matched_by.add(matched_by)

    def _merge_asset_candidate(
        self,
        candidates: dict[UUID, AssetCandidateAccumulator],
        asset: Asset,
        matched_by: str,
        observed_ip: str | None = None,
    ) -> None:
        candidate = candidates.get(asset.id)
        if candidate is None:
            candidate = AssetCandidateAccumulator(asset=asset)
            candidates[asset.id] = candidate
        candidate.matched_by.add(matched_by)
        if observed_ip:
            candidate.observed_ips.add(observed_ip)

    def _serialize_asset_candidates(
        self,
        asset_candidates: dict[UUID, AssetCandidateAccumulator],
    ) -> list[CandidateAssetResponse]:
        responses = [
            CandidateAssetResponse(
                id=candidate.asset.id,
                asset_tag=candidate.asset.asset_tag,
                hostname=candidate.asset.hostname,
                device_type=candidate.asset.device_type,
                owner_display_name=(
                    candidate.asset.owner_user.display_name if candidate.asset.owner_user is not None else None
                ),
                primary_user_display_name=(
                    candidate.asset.primary_user.display_name
                    if candidate.asset.primary_user is not None
                    else None
                ),
                observed_ips=sorted(candidate.observed_ips),
                matched_by=sorted(candidate.matched_by),
            )
            for candidate in asset_candidates.values()
        ]
        return sorted(responses, key=lambda item: (item.hostname.casefold(), item.asset_tag.casefold()))

    def _serialize_user_candidates(
        self,
        user_candidates: dict[UUID, UserCandidateAccumulator],
    ) -> list[CandidateUserResponse]:
        responses = [
            CandidateUserResponse(
                id=candidate.user.id,
                username=candidate.user.username,
                display_name=candidate.user.display_name,
                email=candidate.user.email,
                department=candidate.user.department,
                matched_by=sorted(candidate.matched_by),
            )
            for candidate in user_candidates.values()
        ]
        return sorted(responses, key=lambda item: (item.display_name.casefold(), item.username.casefold()))

    def _build_attribution_preview(
        self,
        payload: CorrelateRequest,
        candidate_users: list[CandidateUserResponse],
    ) -> AttributionPreviewResponse | None:
        if payload.query_type == CorrelateQueryType.IP and is_external_public_ip(payload.query_value):
            return AttributionPreviewResponse(
                actor_type=ActorType.EXTERNAL_UNKNOWN,
                display_name=EXTERNAL_UNKNOWN_DISPLAY_NAME,
                observed_ip=payload.query_value,
                confidence_score=0,
                confidence_grade=EXTERNAL_UNKNOWN_GRADE,
                rationale="External public IP correlations remain conservatively unresolved in Phase 1.",
                next_step=EXTERNAL_UNKNOWN_NEXT_STEP,
            )

        if len(candidate_users) != 1:
            return None

        candidate = candidate_users[0]
        rationale_basis = ", ".join(candidate.matched_by)
        return AttributionPreviewResponse(
            actor_type=ActorType.INTERNAL_USER,
            display_name=candidate.display_name,
            observed_ip=payload.query_value if payload.query_type == CorrelateQueryType.IP else None,
            confidence_score=0.4,
            confidence_grade="C",
            rationale=f"Single internal user candidate derived from {rationale_basis}.",
            next_step=INTERNAL_PREVIEW_NEXT_STEP,
        )
