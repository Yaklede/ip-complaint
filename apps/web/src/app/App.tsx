import { Navigate, Route, Routes } from "react-router-dom";
import { WarningBanner } from "../components/WarningBanner";
import { CaseDetailPage } from "../pages/CaseDetailPage";
import { CaseListPage } from "../pages/CaseListPage";

export function App() {
  return (
    <div className="app-shell">
      <WarningBanner />
      <header className="app-header">
        <div>
          <p className="eyebrow">Internal Investigation Workspace</p>
          <h1>Incident Attribution Suite</h1>
        </div>
        <p className="app-subtitle">
          사건 단위의 증거 보존, 외부 행위자 보수 표기, 검토 전제 문서화를 위한 Phase 1 기반 화면입니다.
        </p>
      </header>

      <main className="app-content">
        <Routes>
          <Route path="/" element={<Navigate to="/cases" replace />} />
          <Route path="/cases" element={<CaseListPage />} />
          <Route path="/cases/:caseId" element={<CaseDetailPage />} />
        </Routes>
      </main>
    </div>
  );
}
