from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.entities import Asset, AssetNetworkBinding, User


def _ingest_internal_event(client: TestClient) -> str:
    response = client.post(
        "/v1/events:ingest",
        json={
            "sourceName": "vpn-prod",
            "sourceType": "VPN",
            "collectedAt": "2026-03-15T03:15:00Z",
            "payload": [
                {
                    "eventTime": "2026-03-15T03:11:20Z",
                    "eventType": "vpn_login",
                    "srcIp": "10.10.20.15",
                    "dstIp": "10.0.2.15",
                    "hostname": "ws-001",
                    "username": "alice",
                    "sessionId": "sess-01",
                    "requestHost": "vpn.internal.example",
                    "requestPath": "/auth",
                    "statusCode": 200,
                    "bytesSent": 1024,
                }
            ],
        },
    )
    assert response.status_code == 201
    return response.json()["eventIds"][0]


def test_post_search_correlate_returns_related_records_and_internal_preview(
    client: TestClient,
    db_session: Session,
) -> None:
    user = User(
        username="alice",
        display_name="Alice Kim",
        email="alice@example.com",
        department="IR",
    )
    db_session.add(user)
    db_session.flush()

    asset = Asset(
        asset_tag="AST-001",
        hostname="ws-001",
        device_type="workstation",
        owner_user_id=user.id,
        primary_user_id=user.id,
    )
    db_session.add(asset)
    db_session.flush()

    db_session.add(
        AssetNetworkBinding(
            asset_id=asset.id,
            ip="10.10.20.15",
            lease_start=datetime(2026, 3, 15, 0, 0, tzinfo=timezone.utc),
            lease_end=datetime(2026, 3, 15, 23, 59, tzinfo=timezone.utc),
        )
    )
    db_session.commit()

    event_id = _ingest_internal_event(client)
    create_case_response = client.post(
        "/v1/cases",
        json={
            "title": "내부 후보 상관분석",
            "eventIds": [event_id],
        },
    )
    assert create_case_response.status_code == 201

    response = client.post(
        "/v1/search/correlate",
        json={
            "queryType": "ip",
            "queryValue": "10.10.20.15",
            "timeFrom": "2026-03-15T00:00:00Z",
            "timeTo": "2026-03-15T23:59:59Z",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["relatedEvents"]) == 1
    assert body["relatedEvents"][0]["username"] == "alice"
    assert len(body["relatedCases"]) == 1
    assert body["relatedCases"][0]["title"] == "내부 후보 상관분석"
    assert len(body["candidateAssets"]) == 1
    assert body["candidateAssets"][0]["hostname"] == "ws-001"
    assert "network_binding" in body["candidateAssets"][0]["matchedBy"]
    assert body["candidateAssets"][0]["primaryUserDisplayName"] == "Alice Kim"
    assert len(body["candidateUsers"]) == 1
    assert body["candidateUsers"][0]["username"] == "alice"
    assert "event_username" in body["candidateUsers"][0]["matchedBy"]
    assert body["attributionPreview"]["actorType"] == "INTERNAL_USER"
    assert body["attributionPreview"]["displayName"] == "Alice Kim"
    assert body["attributionPreview"]["confidenceGrade"] == "C"


def test_post_search_correlate_preserves_external_unknown_for_public_ip(
    client: TestClient,
    sample_event_payload: list[dict[str, object]],
) -> None:
    ingest_response = client.post(
        "/v1/events:ingest",
        json={
            "sourceName": "waf-prod",
            "sourceType": "WAF",
            "collectedAt": "2026-03-15T03:15:00Z",
            "payload": sample_event_payload,
        },
    )
    assert ingest_response.status_code == 201

    response = client.post(
        "/v1/search/correlate",
        json={
            "queryType": "ip",
            "queryValue": "203.0.113.10",
            "timeFrom": "2026-03-15T00:00:00Z",
            "timeTo": "2026-03-15T23:59:59Z",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["relatedEvents"]) == 1
    assert body["attributionPreview"]["actorType"] == "EXTERNAL_UNKNOWN"
    assert body["attributionPreview"]["displayName"] == "성명불상"
    assert body["attributionPreview"]["confidenceGrade"] == "D"
    assert body["attributionPreview"]["nextStep"] == "통신사/플랫폼/수사기관 조회 필요"
