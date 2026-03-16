import type {
  CaseDetail,
  CaseListResponse,
  CaseSummary,
  HealthResponse,
  UpdateCaseRequest,
} from "@incident-attribution/contracts";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-Actor": "web-ui",
      "X-Roles": "investigator,lead,admin,auditor",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

export const apiClient = {
  getHealth: () => request<HealthResponse>("/healthz"),
  listCases: () => request<CaseListResponse>("/v1/cases"),
  getCase: (caseId: string) => request<CaseDetail>(`/v1/cases/${caseId}`),
  updateCase: (caseId: string, payload: UpdateCaseRequest) =>
    request<CaseSummary>(`/v1/cases/${caseId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
};
