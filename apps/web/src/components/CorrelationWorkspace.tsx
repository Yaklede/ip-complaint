import type {
  CorrelateQueryType,
  CorrelateResponse,
} from "@incident-attribution/contracts";
import { useState } from "react";
import { Link } from "react-router-dom";
import { apiClient } from "../shared/api";

type SearchFormState = {
  queryType: CorrelateQueryType;
  queryValue: string;
  timeFrom: string;
  timeTo: string;
};

const QUERY_OPTIONS: Array<{ value: CorrelateQueryType; label: string }> = [
  { value: "ip", label: "IP" },
  { value: "username", label: "Username" },
  { value: "hostname", label: "Hostname" },
  { value: "session", label: "Session" },
  { value: "domain", label: "Domain" },
];

function toLocalDateTimeInput(date: Date): string {
  const timezoneOffsetMs = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - timezoneOffsetMs).toISOString().slice(0, 16);
}

function createDefaultForm(): SearchFormState {
  const timeTo = new Date();
  const timeFrom = new Date(timeTo.getTime() - 24 * 60 * 60 * 1000);
  return {
    queryType: "ip",
    queryValue: "",
    timeFrom: toLocalDateTimeInput(timeFrom),
    timeTo: toLocalDateTimeInput(timeTo),
  };
}

export function CorrelationWorkspace() {
  const [form, setForm] = useState<SearchFormState>(() => createDefaultForm());
  const [result, setResult] = useState<CorrelateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h2>Correlation Search</h2>
          <p className="muted">
            관련 이벤트, 사건, candidate asset/user, 보수적 attribution preview를 한 번에 조회합니다.
          </p>
        </div>
        <span className="count-pill">{loading ? "searching" : "phase-1"}</span>
      </div>

      <form
        className="case-form"
        onSubmit={async (event) => {
          event.preventDefault();
          setLoading(true);
          setError(null);

          try {
            const response = await apiClient.correlate({
              queryType: form.queryType,
              queryValue: form.queryValue,
              timeFrom: new Date(form.timeFrom).toISOString(),
              timeTo: new Date(form.timeTo).toISOString(),
            });
            setResult(response);
          } catch (loadError) {
            setResult(null);
            setError(loadError instanceof Error ? loadError.message : "Unknown error");
          } finally {
            setLoading(false);
          }
        }}
      >
        <label>
          <span>Query Type</span>
          <select
            value={form.queryType}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                queryType: event.target.value as CorrelateQueryType,
              }))
            }
          >
            {QUERY_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Query Value</span>
          <input
            value={form.queryValue}
            onChange={(event) =>
              setForm((current) => ({ ...current, queryValue: event.target.value }))
            }
            placeholder="203.0.113.10 / alice / ws-001"
            required
          />
        </label>

        <label>
          <span>Time From</span>
          <input
            type="datetime-local"
            value={form.timeFrom}
            onChange={(event) => setForm((current) => ({ ...current, timeFrom: event.target.value }))}
            required
          />
        </label>

        <label>
          <span>Time To</span>
          <input
            type="datetime-local"
            value={form.timeTo}
            onChange={(event) => setForm((current) => ({ ...current, timeTo: event.target.value }))}
            required
          />
        </label>

        <button className="primary-button" type="submit" disabled={loading}>
          {loading ? "Searching..." : "Run Correlation"}
        </button>
      </form>

      {error ? <p className="error-text search-feedback">{error}</p> : null}

      {result ? (
        <div className="panel-stack search-results">
          <div className="result-summary-grid">
            <article className="detail-card">
              <p className="eyebrow">Events</p>
              <h3>{result.relatedEvents.length}</h3>
              <p className="muted">지정 구간에 일치한 정규화 이벤트 수</p>
            </article>
            <article className="detail-card">
              <p className="eyebrow">Cases</p>
              <h3>{result.relatedCases.length}</h3>
              <p className="muted">연결된 사건 및 후속 조사 단위</p>
            </article>
            <article className="detail-card">
              <p className="eyebrow">Candidates</p>
              <h3>
                {result.candidateAssets.length} / {result.candidateUsers.length}
              </h3>
              <p className="muted">asset / user summary 후보 수</p>
            </article>
          </div>

          <section className="panel soft-panel">
            <div className="panel-heading">
              <h2>Attribution Preview</h2>
            </div>
            {result.attributionPreview ? (
              <article className="detail-card">
                <p className="eyebrow">{result.attributionPreview.actorType}</p>
                <h3>{result.attributionPreview.displayName}</h3>
                <p className="muted">
                  Grade {result.attributionPreview.confidenceGrade} · score{" "}
                  {result.attributionPreview.confidenceScore}
                </p>
                <p>{result.attributionPreview.rationale ?? "추가 설명 없음"}</p>
                {result.attributionPreview.nextStep ? (
                  <p className="note-box">{result.attributionPreview.nextStep}</p>
                ) : null}
              </article>
            ) : (
              <p className="muted">
                단일 후보로 수렴하지 않아 preview를 생략했습니다. candidate asset/user와 관련 사건을
                함께 검토해야 합니다.
              </p>
            )}
          </section>

          <section className="panel soft-panel">
            <div className="panel-heading">
              <h2>Related Cases</h2>
              <span className="count-pill">{result.relatedCases.length} linked</span>
            </div>
            {result.relatedCases.length === 0 ? (
              <p className="muted">연결된 사건이 없습니다.</p>
            ) : (
              <div className="detail-list">
                {result.relatedCases.map((item) => (
                  <Link key={item.id} to={`/cases/${item.id}`} className="detail-card">
                    <p className="eyebrow">{item.caseNo}</p>
                    <h3>{item.title}</h3>
                    <p className="muted">{item.summary ?? "요약 없음"}</p>
                    <p className="detail-inline">
                      {item.status} · {item.severity}
                    </p>
                  </Link>
                ))}
              </div>
            )}
          </section>

          <section className="panel soft-panel split-panel">
            <div>
              <div className="panel-heading">
                <h2>Candidate Assets</h2>
              </div>
              {result.candidateAssets.length === 0 ? (
                <p className="muted">candidate asset가 없습니다.</p>
              ) : (
                <div className="detail-list">
                  {result.candidateAssets.map((item) => (
                    <article key={item.id} className="detail-card">
                      <p className="eyebrow">{item.assetTag}</p>
                      <h3>{item.hostname}</h3>
                      <p className="muted">{item.deviceType}</p>
                      <p className="detail-inline">
                        Primary {item.primaryUserDisplayName ?? "-"} · Owner {item.ownerDisplayName ?? "-"}
                      </p>
                      <p className="chip-row">
                        {item.observedIps.length > 0 ? item.observedIps.join(", ") : "No observed IP"}
                      </p>
                      <p className="muted">matched by: {item.matchedBy.join(", ")}</p>
                    </article>
                  ))}
                </div>
              )}
            </div>

            <div>
              <div className="panel-heading">
                <h2>Candidate Users</h2>
              </div>
              {result.candidateUsers.length === 0 ? (
                <p className="muted">candidate user가 없습니다.</p>
              ) : (
                <div className="detail-list">
                  {result.candidateUsers.map((item) => (
                    <article key={item.id} className="detail-card">
                      <p className="eyebrow">{item.username}</p>
                      <h3>{item.displayName}</h3>
                      <p className="muted">
                        {item.department ?? "부서 미상"} · {item.email ?? "email 없음"}
                      </p>
                      <p className="muted">matched by: {item.matchedBy.join(", ")}</p>
                    </article>
                  ))}
                </div>
              )}
            </div>
          </section>

          <section className="panel soft-panel">
            <div className="panel-heading">
              <h2>Related Events</h2>
              <span className="count-pill">{result.relatedEvents.length} event(s)</span>
            </div>
            {result.relatedEvents.length === 0 ? (
              <p className="muted">관련 이벤트가 없습니다.</p>
            ) : (
              <ul className="timeline">
                {result.relatedEvents.map((item) => (
                  <li key={item.id}>
                    <div>
                      <strong>{item.eventType}</strong>
                      <p className="muted">
                        {item.eventTime} · {item.srcIp ?? "-"} → {item.dstIp ?? item.requestHost ?? "-"}
                      </p>
                    </div>
                    <span className="timeline-code">{item.sourceType ?? "UNKNOWN"}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      ) : null}
    </section>
  );
}
