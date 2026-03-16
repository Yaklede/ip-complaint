import type { CaseSummary, HealthResponse } from "@incident-attribution/contracts";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { CorrelationWorkspace } from "../components/CorrelationWorkspace";
import { apiClient } from "../shared/api";

export function CaseListPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [healthResult, caseResult] = await Promise.all([
          apiClient.getHealth(),
          apiClient.listCases(),
        ]);
        if (cancelled) {
          return;
        }
        setHealth(healthResult);
        setCases(caseResult.items);
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Unknown error");
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="panel-stack">
      <section className="panel">
        <div className="panel-heading">
          <h2>Case Queue</h2>
          <span className={`status-pill ${health?.status ?? "unknown"}`}>
            API {health?.status ?? "loading"}
          </span>
        </div>
        <p className="muted">
          Phase 1에서는 사건 목록과 상세 화면에 더해 기본 상관분석 검색을 제공합니다. 결과는 모두
          draft/review 전제의 참고 정보입니다.
        </p>
      </section>

      <CorrelationWorkspace />

      <section className="panel">
        <div className="panel-heading">
          <h2>Cases</h2>
          <span className="count-pill">{cases.length} item(s)</span>
        </div>

        {error ? <p className="error-text">{error}</p> : null}

        {!error && cases.length === 0 ? (
          <div className="empty-state">
            <p>등록된 사건이 없습니다.</p>
            <p className="muted">`POST /v1/cases`로 seed case를 생성하면 이 화면에 표시됩니다.</p>
          </div>
        ) : null}

        {cases.length > 0 ? (
          <div className="case-grid">
            {cases.map((item) => (
              <Link key={item.id} to={`/cases/${item.id}`} className="case-card">
                <div className="case-card-top">
                  <span className="eyebrow">{item.caseNo}</span>
                  <span className="severity-chip">{item.severity}</span>
                </div>
                <h3>{item.title}</h3>
                <p className="muted clamp-two">{item.summary ?? "요약 없음"}</p>
                <dl className="meta-list">
                  <div>
                    <dt>Status</dt>
                    <dd>{item.status}</dd>
                  </div>
                  <div>
                    <dt>Primary IP</dt>
                    <dd>{item.primaryIp ?? "-"}</dd>
                  </div>
                  <div>
                    <dt>Actor Label</dt>
                    <dd>{item.externalActorLabel ?? "-"}</dd>
                  </div>
                </dl>
              </Link>
            ))}
          </div>
        ) : null}
      </section>
    </section>
  );
}
