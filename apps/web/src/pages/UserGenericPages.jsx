import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import UserLayout from '../components/UserLayout';
import { apiFetch, formEncoded, getCookie } from '../utils/http';

function ApiError({ error }) {
  if (!error) return null;
  return <p className="pn-err">{error}</p>;
}

function Loading({ loading }) {
  if (!loading) return null;
  return <p className="pn-sub">불러오는 중...</p>;
}

export function HomePage() {
  const [summary, setSummary] = useState(null);
  const [projects, setProjects] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([apiFetch('/api/v1/dashboard/summary'), apiFetch('/api/v1/projects')])
      .then(([s, p]) => {
        setSummary(s);
        setProjects(Array.isArray(p) ? p.slice(0, 5) : []);
      })
      .catch((e) => setError(e.message));
  }, []);

  return (
    <UserLayout title="워크플로우 홈">
      <ApiError error={error} />
      <section className="pn-grid3" style={{ marginBottom: 12 }}>
        <article className="pn-card"><div className="pn-sub">기관</div><h3>{summary?.teams ?? '-'}</h3></article>
        <article className="pn-card"><div className="pn-sub">프로젝트</div><h3>{summary?.projects ?? '-'}</h3></article>
        <article className="pn-card"><div className="pn-sub">연구노트</div><h3>{summary?.notes ?? '-'}</h3></article>
      </section>
      <section className="pn-card">
        <h3 style={{ marginTop: 0 }}>최근 프로젝트</h3>
        <table className="pn-table">
          <thead><tr><th>이름</th><th>상태</th><th>기관</th></tr></thead>
          <tbody>
            {projects.map((p) => <tr key={p.id}><td>{p.name}</td><td>{p.status}</td><td>{p.organization || '-'}</td></tr>)}
            {projects.length === 0 && <tr><td colSpan={3} className="pn-sub">데이터가 없습니다.</td></tr>}
          </tbody>
        </table>
      </section>
    </UserLayout>
  );
}

export function ProjectsPage() {
  const [projects, setProjects] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    apiFetch('/api/v1/projects').then((rows) => setProjects(Array.isArray(rows) ? rows : [])).catch((e) => setError(e.message));
  }, []);

  return (
    <UserLayout title="프로젝트 통합 관리">
      <ApiError error={error} />
      <section className="pn-card">
        <p className="pn-sub">프로젝트를 클릭하면 해당 프로젝트 연구노트 관리 화면으로 이동합니다.</p>
        <table className="pn-table">
          <thead><tr><th>프로젝트</th><th>코드</th><th>상태</th><th>매니저</th><th>기관</th></tr></thead>
          <tbody>
            {projects.map((p) => (
              <tr key={p.id}>
                <td><Link className="pn-link" to={`/projects/${p.id}/research-notes`}>{p.name}</Link></td>
                <td>{p.code}</td><td>{p.status}</td><td>{p.manager}</td><td>{p.organization || '-'}</td>
              </tr>
            ))}
            {projects.length === 0 && <tr><td colSpan={5} className="pn-sub">프로젝트가 없습니다.</td></tr>}
          </tbody>
        </table>
      </section>
    </UserLayout>
  );
}

export function ProjectCreatePage() {
  const nav = useNavigate();
  const [form, setForm] = useState({ name: '', manager: '', business_name: '', organization: '', code: '', description: '', status: 'draft' });
  const [error, setError] = useState('');
  const [msg, setMsg] = useState('');

  async function submit(e) {
    e.preventDefault();
    setError('');
    setMsg('');
    try {
      const created = await apiFetch('/api/v1/project-management', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': getCookie('csrftoken') },
        body: formEncoded(form)
      });
      setMsg(`생성 완료: ${created.name}`);
      if (created.id) setTimeout(() => nav(`/projects/${created.id}`), 600);
    } catch (e2) {
      setError(e2.message);
    }
  }

  return (
    <UserLayout title="프로젝트 생성">
      <section className="pn-card">
        <form className="pn-grid" onSubmit={submit} style={{ gap: 8 }}>
          <input placeholder="프로젝트명" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          <input placeholder="매니저(username)" value={form.manager} onChange={(e) => setForm({ ...form, manager: e.target.value })} />
          <input placeholder="사업명" value={form.business_name} onChange={(e) => setForm({ ...form, business_name: e.target.value })} />
          <input placeholder="기관" value={form.organization} onChange={(e) => setForm({ ...form, organization: e.target.value })} />
          <input placeholder="코드" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} />
          <input placeholder="설명" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
            <option value="draft">draft</option><option value="active">active</option><option value="completed">completed</option>
          </select>
          <button type="submit">생성</button>
        </form>
        <ApiError error={error} />
        {msg && <p className="pn-sub">{msg}</p>}
      </section>
    </UserLayout>
  );
}

export function ProjectDetailPage() {
  const { id } = useParams();
  const [project, setProject] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    apiFetch('/api/v1/projects')
      .then((rows) => {
        const found = Array.isArray(rows) ? rows.find((r) => String(r.id) === String(id)) : null;
        setProject(found || null);
      })
      .catch((e) => setError(e.message));
  }, [id]);

  return (
    <UserLayout title="프로젝트 상세">
      <ApiError error={error} />
      <section className="pn-card">
        {project ? (
          <table className="pn-table"><tbody>
            <tr><th>ID</th><td>{project.id}</td></tr>
            <tr><th>이름</th><td>{project.name}</td></tr>
            <tr><th>코드</th><td>{project.code}</td></tr>
            <tr><th>상태</th><td>{project.status}</td></tr>
            <tr><th>매니저</th><td>{project.manager}</td></tr>
            <tr><th>기관</th><td>{project.organization || '-'}</td></tr>
            <tr><th>설명</th><td>{project.description || '-'}</td></tr>
          </tbody></table>
        ) : <p className="pn-sub">프로젝트를 찾을 수 없습니다.</p>}
      </section>
    </UserLayout>
  );
}

export function ResearchersPage() {
  return (
    <UserLayout title="연구원 통합 관리">
      <ResearchersPageTable />
    </UserLayout>
  );
}

export function ProjectResearchersPage() {
  const { id } = useParams();
  return (
    <UserLayout title="프로젝트 연구원">
      <section className="pn-card">
        <p className="pn-sub" style={{ margin: 0 }}>프로젝트 #{id} 기준 연구원 화면입니다.</p>
      </section>
      <ResearchersPageTable />
    </UserLayout>
  );
}

function ResearchersPageTable() {
  const [rows, setRows] = useState([]);
  const [error, setError] = useState('');
  useEffect(() => { apiFetch('/api/v1/researchers').then((r) => setRows(Array.isArray(r) ? r : [])).catch((e) => setError(e.message)); }, []);

  return (
    <section className="pn-card">
      <ApiError error={error} />
      <table className="pn-table"><thead><tr><th>이름</th><th>역할</th><th>이메일</th><th>기관</th><th>상태</th></tr></thead><tbody>
        {rows.map((r) => <tr key={r.id}><td>{r.name}</td><td>{r.role}</td><td>{r.email}</td><td>{r.organization}</td><td>{r.status}</td></tr>)}
      </tbody></table>
    </section>
  );
}

function NotesTable({ endpoint }) {
  const [rows, setRows] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    setLoading(true);
    apiFetch(endpoint).then((r) => setRows(Array.isArray(r) ? r : [])).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, [endpoint]);

  return (
    <section className="pn-card">
      <Loading loading={loading} />
      <ApiError error={error} />
      <table className="pn-table">
        <thead><tr><th>제목</th><th>작성자</th><th>프로젝트 코드</th><th>기간</th><th>파일수</th></tr></thead>
        <tbody>
          {rows.map((n) => <tr key={n.id}><td>{n.title}</td><td>{n.owner}</td><td>{n.project_code}</td><td>{n.period}</td><td>{n.files}</td></tr>)}
          {rows.length === 0 && !loading && <tr><td colSpan={5} className="pn-sub">연구노트가 없습니다.</td></tr>}
        </tbody>
      </table>
    </section>
  );
}

export function ProjectResearchNotesPage() {
  const { id } = useParams();
  const [project, setProject] = useState(null);

  useEffect(() => {
    apiFetch('/api/v1/projects').then((rows) => {
      const found = Array.isArray(rows) ? rows.find((r) => String(r.id) === String(id)) : null;
      setProject(found || null);
    }).catch(() => setProject(null));
  }, [id]);

  return (
    <UserLayout title="프로젝트 연구노트">
      <section className="pn-card">
        <h3>{project?.name || `프로젝트 #${id}`}</h3>
        <p className="pn-sub" style={{ margin: 0 }}>선택한 프로젝트 기준 연구노트 화면입니다.</p>
      </section>
      <NotesTable endpoint="/api/v1/research-notes" />
    </UserLayout>
  );
}
export function ProjectResearchNotesPrintPage() { return <UserLayout title="프로젝트 연구노트 인쇄"><NotesTable endpoint="/api/v1/research-notes" /></UserLayout>; }
export function ResearchNotesListPage() { return <UserLayout title="연구노트 목록"><NotesTable endpoint="/api/v1/research-notes" /></UserLayout>; }

function ResearchNoteDetailCard({ id, title }) {
  const [note, setNote] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => { apiFetch(`/api/v1/research-notes/${id}`).then(setNote).catch((e) => setError(e.message)); }, [id]);
  return (
    <UserLayout title={title}>
      <ApiError error={error} />
      <section className="pn-card">
        <pre className="pn-json">{JSON.stringify(note, null, 2)}</pre>
      </section>
    </UserLayout>
  );
}

export function ResearchNoteDetailPage() { const { id } = useParams(); return <ResearchNoteDetailCard id={id} title="연구노트 상세" />; }
export function ResearchNoteViewerPage() { const { id } = useParams(); return <ResearchNoteDetailCard id={id} title="연구노트 뷰어" />; }
export function ResearchNoteCoverPage() { const { id } = useParams(); return <ResearchNoteDetailCard id={id} title="연구노트 커버" />; }
export function ResearchNotePrintablePage() { const { id } = useParams(); return <ResearchNoteDetailCard id={id} title="연구노트 출력" />; }

export function MyPage() {
  const [sign, setSign] = useState(null);
  const [status, setStatus] = useState('valid');
  const [signatureDataUrl, setSignatureDataUrl] = useState('');
  const [error, setError] = useState('');
  const [msg, setMsg] = useState('');

  useEffect(() => {
    apiFetch('/api/v1/signatures').then((s) => {
      setSign(s);
      setStatus(s?.status || 'valid');
      setSignatureDataUrl(s?.signature_data_url || '');
    }).catch((e) => setError(e.message));
  }, []);

  function onPickSignature(file) {
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      setError('이미지 파일만 업로드할 수 있습니다.');
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      setError('');
      setMsg('새 서명 이미지를 선택했습니다. 저장 버튼을 눌러 반영하세요.');
      setSignatureDataUrl(String(reader.result || ''));
    };
    reader.readAsDataURL(file);
  }

  async function saveSignature() {
    setError('');
    setMsg('');
    if (!signatureDataUrl) {
      setError('서명 이미지를 먼저 선택해주세요.');
      return;
    }
    try {
      const updated = await apiFetch('/api/v1/signatures', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': getCookie('csrftoken') },
        body: formEncoded({ status, signature_data_url: signatureDataUrl })
      });
      setSign(updated);
      setStatus(updated?.status || status);
      setSignatureDataUrl(updated?.signature_data_url || signatureDataUrl);
      setMsg('개인 서명이 저장되었습니다.');
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <UserLayout title="마이페이지">
      <ApiError error={error} />
      {msg && <p className="pn-sub">{msg}</p>}
      <section className="pn-card">
        <h3 style={{ marginTop: 0 }}>개인 서명</h3>
        <p>서명자: {sign?.last_signed_by || '-'}</p>
        <p>최근 서명일: {sign?.last_signed_at || '-'}</p>
        <p>현재 상태: {sign?.status || '-'}</p>

        <label className="pn-upload-zone" htmlFor="signatureFileInput" onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); onPickSignature(e.dataTransfer.files?.[0]); }}>
          {signatureDataUrl ? (
            <img alt="전자서명" className="pn-signature-preview" src={signatureDataUrl} />
          ) : (
            <span className="pn-sub" style={{ margin: 0 }}>드래그 앤 드롭 또는 클릭으로 서명 이미지를 올려주세요.</span>
          )}
        </label>
        <input
          accept="image/*"
          id="signatureFileInput"
          onChange={(e) => onPickSignature(e.target.files?.[0])}
          style={{ display: 'none' }}
          type="file"
        />

        <div className="pn-inline">
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="valid">valid</option>
            <option value="pending">pending</option>
            <option value="expired">expired</option>
          </select>
          <button type="button" onClick={saveSignature}>서명 저장</button>
        </div>
      </section>
    </UserLayout>
  );
}

export function DataUpdatesPage() {
  const [rows, setRows] = useState([]);
  const [error, setError] = useState('');
  useEffect(() => { apiFetch('/api/v1/data-updates').then((r) => setRows(Array.isArray(r) ? r : [])).catch((e) => setError(e.message)); }, []);
  return (
    <UserLayout title="활동내역">
      <ApiError error={error} />
      <section className="pn-card"><table className="pn-table"><thead><tr><th>ID</th><th>대상</th><th>상태</th><th>업데이트시각</th></tr></thead><tbody>
        {rows.map((r) => <tr key={r.id}><td>{r.id}</td><td>{r.target}</td><td>{r.status}</td><td>{r.updated_at}</td></tr>)}
      </tbody></table></section>
    </UserLayout>
  );
}

export function GithubIntegrationsPage() {
  return (
    <UserLayout title="GitHub 연동">
      <section className="pn-card"><p className="pn-sub">GitHub/협업 연동 상세 기능은 다음 단계에서 연결합니다.</p></section>
    </UserLayout>
  );
}

