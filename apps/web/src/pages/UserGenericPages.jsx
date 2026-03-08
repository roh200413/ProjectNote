import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import UserLayout from '../components/UserLayout';
import { apiFetch } from '../utils/http';

function DataPanel({ title, endpoint, transform }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    apiFetch(endpoint)
      .then((res) => setData(transform ? transform(res) : res))
      .catch((e) => setError(e.message));
  }, [endpoint, transform]);

  return (
    <section className="pn-card">
      <h3 style={{ marginTop: 0 }}>{title}</h3>
      {error && <p className="pn-err">{error}</p>}
      <pre className="pn-json">{JSON.stringify(data, null, 2)}</pre>
    </section>
  );
}

export function HomePage() {
  return (
    <UserLayout title="워크플로우 홈">
      <div className="pn-grid2">
        <DataPanel title="대시보드 요약" endpoint="/api/v1/dashboard/summary" />
        <DataPanel title="프로젝트 목록" endpoint="/api/v1/projects" />
      </div>
    </UserLayout>
  );
}

export function ProjectsPage() {
  return (
    <UserLayout title="프로젝트 관리">
      <DataPanel title="프로젝트 목록" endpoint="/api/v1/projects" />
    </UserLayout>
  );
}

export function ProjectDetailPage() {
  const { id } = useParams();
  const transform = useCallback((rows) => (Array.isArray(rows) ? rows.find((r) => String(r.id) === String(id)) : rows), [id]);
  return (
    <UserLayout title="프로젝트 상세">
      <DataPanel title={`프로젝트 ${id} 상세(목록 필터)`} endpoint="/api/v1/projects" transform={transform} />
    </UserLayout>
  );
}

export function ProjectCreatePage() {
  return (
    <UserLayout title="프로젝트 생성">
      <section className="pn-card"><p className="pn-sub">프로젝트 생성 React 폼은 다음 단계에서 상세 필드로 확장 예정입니다.</p></section>
    </UserLayout>
  );
}

export function ResearchersPage() {
  return <UserLayout title="연구자 관리"><DataPanel title="연구자 목록" endpoint="/api/v1/researchers" /></UserLayout>;
}

export function ProjectResearchersPage() {
  const { id } = useParams();
  return <UserLayout title="프로젝트 참여 연구자"><DataPanel title={`프로젝트 ${id} 참여 연구자`} endpoint="/api/v1/researchers" /></UserLayout>;
}

export function ProjectResearchNotesPage() {
  const { id } = useParams();
  return <UserLayout title="프로젝트 연구노트"><DataPanel title={`프로젝트 ${id} 연구노트`} endpoint="/api/v1/research-notes" /></UserLayout>;
}

export function ProjectResearchNotesPrintPage() {
  const { id } = useParams();
  return <UserLayout title="프로젝트 연구노트 인쇄"><DataPanel title={`프로젝트 ${id} 연구노트(인쇄용)`} endpoint="/api/v1/research-notes" /></UserLayout>;
}

export function ResearchNotesListPage() {
  return <UserLayout title="연구노트 목록"><DataPanel title="연구노트 목록" endpoint="/api/v1/research-notes" /></UserLayout>;
}

export function ResearchNoteDetailPage() {
  const { id } = useParams();
  return <UserLayout title="연구노트 상세"><DataPanel title={`연구노트 ${id}`} endpoint={`/api/v1/research-notes/${id}`} /></UserLayout>;
}

export function ResearchNoteViewerPage() {
  const { id } = useParams();
  return <UserLayout title="연구노트 뷰어"><DataPanel title={`연구노트 ${id} 뷰어 데이터`} endpoint={`/api/v1/research-notes/${id}`} /></UserLayout>;
}

export function ResearchNoteCoverPage() {
  const { id } = useParams();
  return <UserLayout title="연구노트 커버"><DataPanel title={`연구노트 ${id} 커버 데이터`} endpoint={`/api/v1/research-notes/${id}`} /></UserLayout>;
}

export function ResearchNotePrintablePage() {
  const { id } = useParams();
  return <UserLayout title="연구노트 출력"><DataPanel title={`연구노트 ${id} 출력 데이터`} endpoint={`/api/v1/research-notes/${id}`} /></UserLayout>;
}

export function MyPage() {
  return (
    <UserLayout title="마이페이지">
      <div className="pn-grid2">
        <DataPanel title="부트스트랩" endpoint="/api/v1/frontend/bootstrap" />
        <DataPanel title="내 서명" endpoint="/api/v1/signatures" />
      </div>
    </UserLayout>
  );
}

export function DataUpdatesPage() {
  return <UserLayout title="활동내역"><DataPanel title="활동내역" endpoint="/api/v1/data-updates" /></UserLayout>;
}

export function GithubIntegrationsPage() {
  return <UserLayout title="GitHub 연동"><section className="pn-card"><p className="pn-sub">GitHub 연동 설정 화면 React 복구 완료(기능 확장 예정).</p></section></UserLayout>;
}

export function SignaturesPage() {
  return <UserLayout title="서명"><DataPanel title="서명 상태" endpoint="/api/v1/signatures" /></UserLayout>;
}

export function FinalDownloadPage() {
  return <UserLayout title="최종 다운로드"><DataPanel title="최종 다운로드 데이터" endpoint="/api/v1/final-download" /></UserLayout>;
}
