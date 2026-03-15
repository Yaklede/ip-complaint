from __future__ import annotations

from fastapi.testclient import TestClient


def test_healthz_reports_service_and_dependencies(client: TestClient) -> None:
    response = client.get("/healthz")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "Incident Attribution API"
    assert body["dependencies"]["database"]["status"] == "ready"
    assert body["dependencies"]["opensearch"]["status"] == "not_configured"
