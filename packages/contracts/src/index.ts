export type SourceType =
  | "WEB"
  | "WAF"
  | "VPN"
  | "AD"
  | "EDR"
  | "DHCP"
  | "NAT"
  | "FW"
  | "DB"
  | "APP"
  | "OTHER";

export type ActorType =
  | "INTERNAL_USER"
  | "EXTERNAL_UNKNOWN"
  | "SERVICE_ACCOUNT"
  | "SYSTEM";

export type CaseStatus =
  | "NEW"
  | "TRIAGED"
  | "INVESTIGATING"
  | "READY_FOR_REVIEW"
  | "READY_FOR_EXPORT"
  | "CLOSED"
  | "REJECTED";

export type EvidenceStatus = "PENDING" | "FROZEN" | "EXPORTED";
export type DocumentStatus = "DRAFT" | "UNDER_REVIEW" | "APPROVED" | "REJECTED";

export interface DependencyHealth {
  status: string;
  detail?: string | null;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  dependencies: Record<string, DependencyHealth>;
}

export interface IngestRequest {
  sourceName: string;
  sourceType: SourceType;
  collectedAt: string;
  payload: string | Record<string, unknown>[];
  parserVersion?: string;
}

export interface IngestResponse {
  rawArtifactId: string;
  normalizedEventCount: number;
  checksumSha256: string;
  eventIds: string[];
}

export type CorrelateQueryType = "ip" | "username" | "hostname" | "session" | "domain";

export interface NormalizedEvent {
  id: string;
  eventTime: string;
  sourceType?: SourceType | null;
  eventType: string;
  srcIp?: string | null;
  dstIp?: string | null;
  hostname?: string | null;
  username?: string | null;
  sessionId?: string | null;
  requestHost?: string | null;
  requestPath?: string | null;
  statusCode?: number | null;
  bytesSent?: number | null;
  rawArtifactId: string;
}

export interface CreateCaseRequest {
  title: string;
  summary?: string;
  primaryIp?: string;
  eventIds?: string[];
  seedEventIds?: string[];
  notes?: string;
  severity?: string;
}

export interface UpdateCaseRequest {
  title?: string;
  summary?: string;
  status?: CaseStatus;
  severity?: string;
  assignee?: string;
}

export interface CaseSummary {
  id: string;
  caseNo: string;
  title: string;
  status: CaseStatus;
  severity: string;
  primaryIp?: string | null;
  confidenceGrade?: string | null;
  externalActorLabel?: string | null;
  summary?: string | null;
  assignee?: string | null;
  openedAt: string;
}

export interface RelatedEventsSummary {
  totalCount: number;
  firstSeenAt?: string | null;
  lastSeenAt?: string | null;
  sourceTypes: string[];
  eventTypes: string[];
}

export interface AttributionLink {
  id: string;
  actorType: ActorType;
  displayName: string;
  observedIp?: string | null;
  confidenceScore: number;
  confidenceGrade: string;
  rationale?: string | null;
  nextStep?: string | null;
}

export interface EvidenceRecord {
  id: string;
  evidenceType: string;
  rawArtifactId?: string | null;
  normalizedEventId?: string | null;
  objectUri?: string | null;
  sha256: string;
  status: EvidenceStatus;
  frozenAt?: string | null;
  exportedAt?: string | null;
  metadataJson: Record<string, unknown>;
  createdAt: string;
}

export interface DocumentRecord {
  id: string;
  docType: string;
  status: DocumentStatus;
  versionNo: number;
  storageUri?: string | null;
  checksumSha256: string;
  generatedAt: string;
}

export interface CaseDetail extends CaseSummary {
  relatedEventsSummary: RelatedEventsSummary;
  timeline: NormalizedEvent[];
  attributionLinks: AttributionLink[];
  evidence: EvidenceRecord[];
  documents: DocumentRecord[];
}

export interface CaseListResponse {
  items: CaseSummary[];
  total: number;
}

export interface FreezeResponse {
  bundleId: string;
  frozenEvidenceCount: number;
  manifestChecksum: string;
  status: string;
}

export interface ExportResponse {
  bundleId: string;
  exportedEvidenceCount: number;
  manifestChecksum: string;
  status: string;
}

export interface CorrelateRequest {
  queryType: CorrelateQueryType;
  queryValue: string;
  timeFrom: string;
  timeTo: string;
}

export interface CandidateAsset {
  id: string;
  assetTag: string;
  hostname: string;
  deviceType: string;
  ownerDisplayName?: string | null;
  primaryUserDisplayName?: string | null;
  observedIps: string[];
  matchedBy: string[];
}

export interface CandidateUser {
  id: string;
  username: string;
  displayName: string;
  email?: string | null;
  department?: string | null;
  matchedBy: string[];
}

export interface AttributionPreview {
  actorType: ActorType;
  displayName: string;
  observedIp?: string | null;
  confidenceScore: number;
  confidenceGrade: string;
  rationale?: string | null;
  nextStep?: string | null;
}

export interface CorrelateResponse {
  relatedEvents: NormalizedEvent[];
  relatedCases: CaseSummary[];
  candidateAssets: CandidateAsset[];
  candidateUsers: CandidateUser[];
  attributionPreview?: AttributionPreview | null;
}
