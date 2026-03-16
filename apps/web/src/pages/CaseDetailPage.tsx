import type { CaseDetail, CaseStatus, UpdateCaseRequest } from "@incident-attribution/contracts";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { apiClient } from "../shared/api";

const CASE_STATUSES: CaseStatus[] = [
  "NEW",
  "TRIAGED",
  "INVESTIGATING",
  "READY_FOR_REVIEW",
  "READY_FOR_EXPORT",
  "CLOSED",
  "REJECTED",
];

export function CaseDetailPage() {
  const { caseId } = useParams();
  const [caseDetail, setCaseDetail] = useState<CaseDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [updateForm, setUpdateForm] = useState<UpdateCaseRequest>({
    status: "NEW",
    severity: "medium",
    assignee: "",
    summary: "",
  });
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved">("idle");
  const [exportState, setExportState] = useState<"idle" | "preparing" | "prepared">("idle");

  useEffect(() => {
    if (!caseId) {
      return;
    }
    const caseIdValue = caseId;

    let cancelled = false;
    async function load() {
      try {
        const result = await apiClient.getCase(caseIdValue);
        if (!cancelled) {
          setCaseDetail(result);
        }
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
  }, [caseId]);

  useEffect(() => {
    if (!caseDetail) {
      return;
    }

    setUpdateForm({
      status: caseDetail.status,
      severity: caseDetail.severity,
      assignee: caseDetail.assignee ?? "",
      summary: caseDetail.summary ?? "",
    });
  }, [caseDetail]);

  if (!caseId) {
    return <p className="error-text">caseId가 없습니다.</p>;
  }

  if (error) {
    return (
      <section className="panel">
        <Link className="back-link" to="/cases">
          ← 사건 목록으로
        </Link>
        <p className="error-text">{error}</p>
      </section>
    );
  }

  if (!caseDetail) {
    return (
      <section className="panel">
        <Link className="back-link" to="/cases">
          ← 사건 목록으로
        </Link>
        <p className="muted">사건 정보를 불러오는 중입니다.</p>
      </section>
    );
  }

  return (
    <section className="panel-stack">
      <section className="panel">
        <Link className="back-link" to="/cases">
          ← 사건 목록으로
        </Link>
        <div className="panel-heading">
          <div>
            <p className="eyebrow">{caseDetail.caseNo}</p>
            <h2>{caseDetail.title}</h2>
          </div>
          <div className="status-group">
            <span className="status-pill">{caseDetail.status}</span>
            <span className="severity-chip">{caseDetail.severity}</span>
          </div>
        </div>
        <p className="muted">{caseDetail.summary ?? "요약 없음"}</p>
        <dl className="meta-list compact">
          <div>
            <dt>Primary IP</dt>
            <dd>{caseDetail.primaryIp ?? "-"}</dd>
          </div>
          <div>
            <dt>Confidence</dt>
            <dd>{caseDetail.confidenceGrade ?? "-"}</dd>
          </div>
          <div>
            <dt>External Label</dt>
            <dd>{caseDetail.externalActorLabel ?? "-"}</dd>
          </div>
          <div>
            <dt>Events</dt>
            <dd>{caseDetail.relatedEventsSummary.totalCount}</dd>
          </div>
          <div>
            <dt>Assignee</dt>
            <dd>{caseDetail.assignee ?? "-"}</dd>
          </div>
        </dl>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <h2>Case Actions</h2>
          <span className="count-pill">{saveState === "saved" ? "saved" : "editable"}</span>
        </div>
        <form
          className="case-form"
          onSubmit={async (event) => {
            event.preventDefault();
            setSaveState("saving");
            setError(null);
            try {
              await apiClient.updateCase(caseId, updateForm);
              const refreshed = await apiClient.getCase(caseId);
              setCaseDetail(refreshed);
              setSaveState("saved");
            } catch (saveError) {
              setError(saveError instanceof Error ? saveError.message : "Unknown error");
              setSaveState("idle");
            }
          }}
        >
          <label>
            <span>Status</span>
            <select
              value={updateForm.status}
              onChange={(event) =>
                setUpdateForm((current) => ({ ...current, status: event.target.value as CaseStatus }))
              }
            >
              {CASE_STATUSES.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
          </label>

          <label>
            <span>Severity</span>
            <select
              value={updateForm.severity}
              onChange={(event) =>
                setUpdateForm((current) => ({ ...current, severity: event.target.value }))
              }
            >
              <option value="low">low</option>
              <option value="medium">medium</option>
              <option value="high">high</option>
              <option value="critical">critical</option>
            </select>
          </label>

          <label>
            <span>Assignee</span>
            <input
              value={updateForm.assignee ?? ""}
              onChange={(event) =>
                setUpdateForm((current) => ({ ...current, assignee: event.target.value }))
              }
              placeholder="team-or-owner"
            />
          </label>

          <label className="full-width">
            <span>Summary</span>
            <textarea
              value={updateForm.summary ?? ""}
              onChange={(event) =>
                setUpdateForm((current) => ({ ...current, summary: event.target.value }))
              }
              rows={4}
            />
          </label>

          <button className="primary-button" type="submit" disabled={saveState === "saving"}>
            {saveState === "saving" ? "Saving..." : "Save Case"}
          </button>
        </form>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <h2>Attribution Links</h2>
        </div>
        {caseDetail.attributionLinks.length === 0 ? (
          <p className="muted">연결된 귀속 결과가 없습니다.</p>
        ) : (
          <div className="detail-list">
            {caseDetail.attributionLinks.map((link) => (
              <article key={link.id} className="detail-card">
                <p className="eyebrow">{link.actorType}</p>
                <h3>{link.displayName}</h3>
                <p className="muted">{link.rationale ?? "사유 없음"}</p>
                <p className="detail-inline">
                  Grade {link.confidenceGrade} · {link.observedIp ?? "-"}
                </p>
                {link.nextStep ? <p className="note-box">{link.nextStep}</p> : null}
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="panel split-panel">
        <div>
          <div className="panel-heading">
            <h2>Evidence</h2>
          </div>
          {caseDetail.evidence.length === 0 ? (
            <p className="muted">freeze 전이라 증거 목록이 비어 있습니다.</p>
          ) : (
            <ul className="simple-list">
              {caseDetail.evidence.map((item) => (
                <li key={item.id}>
                  <strong>{item.evidenceType}</strong> · {item.status} · {item.sha256.slice(0, 12)}...
                </li>
              ))}
            </ul>
          )}
        </div>

        <div>
          <div className="panel-heading">
            <h2>Documents</h2>
            <button
              className="secondary-button"
              type="button"
              disabled={exportState === "preparing"}
              onClick={async () => {
                setExportState("preparing");
                setError(null);
                try {
                  await apiClient.prepareExport(caseId);
                  const refreshed = await apiClient.getCase(caseId);
                  setCaseDetail(refreshed);
                  setExportState("prepared");
                } catch (exportError) {
                  setError(exportError instanceof Error ? exportError.message : "Unknown error");
                  setExportState("idle");
                }
              }}
            >
              {exportState === "preparing" ? "Preparing..." : "Prepare Export"}
            </button>
          </div>
          {caseDetail.documents.length === 0 ? (
            <p className="muted">생성된 문서가 없습니다.</p>
          ) : (
            <ul className="simple-list">
              {caseDetail.documents.map((item) => (
                <li key={item.id}>
                  <strong>{item.docType}</strong> · {item.status} · v{item.versionNo}
                </li>
              ))}
            </ul>
          )}
          <p className="muted">
            export는 metadata-only draft bundle만 생성하며 최종 제출 문서는 만들지 않습니다.
          </p>
        </div>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <h2>Timeline Preview</h2>
        </div>
        {caseDetail.timeline.length === 0 ? (
          <p className="muted">연결된 이벤트가 없습니다.</p>
        ) : (
          <ul className="timeline">
            {caseDetail.timeline.map((event) => (
              <li key={event.id}>
                <div>
                  <strong>{event.eventType}</strong>
                  <p className="muted">
                    {event.eventTime} · {event.srcIp ?? "-"} → {event.requestHost ?? "-"}
                    {event.requestPath ?? ""}
                  </p>
                </div>
                <span className="timeline-code">{event.sourceType ?? "UNKNOWN"}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </section>
  );
}
