import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import UserLayout from '../components/UserLayout';
import { apiFetch, formEncoded, getCookie } from '../utils/http';
import { saveSelectedProject } from '../utils/projectContext';

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
        setProjects(Array.isArray(p) ? p : []);
      })
      .catch((e) => setError(e.message));
  }, []);

  return (
    <UserLayout title="대시보드">
      <ApiError error={error} />
      <section className="pn-card">
        <h3>내가 관리중인 전체 프로젝트</h3>
        <p className="pn-sub">프로젝트를 클릭하면 좌측 하단에 프로젝트 관련 메뉴가 열립니다.</p>
        <table className="pn-table">
          <thead><tr><th>프로젝트</th><th>상태</th><th>기관</th></tr></thead>
          <tbody>
            {projects.map((p) => <tr key={p.id}><td><Link className="pn-link" onClick={() => saveSelectedProject(p)} to={`/projects/${p.id}/research-notes`}>{p.name}</Link></td><td>{p.status}</td><td>{p.organization || '-'}</td></tr>)}
            {projects.length === 0 && <tr><td colSpan={3} className="pn-sub">관리중인 프로젝트가 없습니다.</td></tr>}
          </tbody>
        </table>
        <div className="pn-inline" style={{ justifyContent: 'flex-end', marginBottom: 0 }}>
          <Link className="pn-side-list" to="/data-updates">활동내역</Link>
          <Link className="pn-side-list active" to="/projects/create">프로젝트 생성</Link>
        </div>
      </section>
      <section className="pn-grid3">
        <article className="pn-card"><div className="pn-sub">프로젝트</div><h3>{summary?.projects ?? '-'}</h3></article>
        <article className="pn-card"><div className="pn-sub">연구노트</div><h3>{summary?.notes ?? '-'}</h3></article>
        <article className="pn-card"><div className="pn-sub">내 프로젝트</div><h3>{projects.length}</h3></article>
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
                <td><Link className="pn-link" onClick={() => saveSelectedProject(p)} to={`/projects/${p.id}/research-notes`}>{p.name}</Link></td>
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
  const [error, setError] = useState('');
  const [msg, setMsg] = useState('');
  const [members, setMembers] = useState([]);
  const [draftMember, setDraftMember] = useState({ username: '', role: 'Member' });
  const [form, setForm] = useState({
    name: '',
    manager: '',
    business_name: '',
    organization: '',
    code: '',
    description: '',
    start_date: '',
    end_date: '',
    status: 'draft'
  });

  function addMember() {
    if (!draftMember.username.trim()) return;
    setMembers([...members, { ...draftMember, username: draftMember.username.trim() }]);
    setDraftMember({ username: '', role: 'Member' });
  }

  async function submit(e) {
    e.preventDefault();
    setError('');
    setMsg('');
    try {
      const created = await apiFetch('/api/v1/project-management', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': getCookie('csrftoken') },
        body: formEncoded({
          ...form,
          period: form.start_date && form.end_date ? `${form.start_date} ~ ${form.end_date}` : '',
          invited_members: JSON.stringify([])
        })
      });
      saveSelectedProject(created);
      setMsg(`프로젝트 생성 완료: ${created.name}`);
      setTimeout(() => nav(`/projects/${created.id}`), 400);
    } catch (e2) {
      setError(e2.message);
    }
  }

  return (
    <UserLayout title="Create Project">
      <ApiError error={error} />
      {msg && <p className="pn-sub">{msg}</p>}
      <form onSubmit={submit}>
        <section className="pn-card">
          <h3>과제 정보</h3>
          <p className="pn-sub">프로젝트 기본 정보를 입력하세요.</p>
          <div className="pn-grid2">
            <div style={{ gridColumn: '1 / -1' }}><label className="pn-sub">과제명</label><input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></div>
            <div><label className="pn-sub">과제 책임자</label><input value={form.manager} onChange={(e) => setForm({ ...form, manager: e.target.value })} /></div>
            <div><label className="pn-sub">사업명</label><input value={form.business_name} onChange={(e) => setForm({ ...form, business_name: e.target.value })} /></div>
            <div><label className="pn-sub">수행 기관</label><input value={form.organization} onChange={(e) => setForm({ ...form, organization: e.target.value })} /></div>
            <div><label className="pn-sub">과제 번호</label><input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} /></div>
            <div><label className="pn-sub">설명</label><input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></div>
            <div><label className="pn-sub">시작일</label><input type="date" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} /></div>
            <div><label className="pn-sub">종료일</label><input type="date" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} /></div>
            <div><label className="pn-sub">상태</label><select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}><option value="draft">draft</option><option value="active">active</option><option value="completed">completed</option></select></div>
          </div>
        </section>

        <section className="pn-card">
          <h3>추가 설정 및 멤버 초대</h3>
          <p className="pn-sub">선택한 사용자는 멤버로 생성됩니다.</p>
          <div className="pn-inline">
            <input placeholder="사용자 아이디" value={draftMember.username} onChange={(e) => setDraftMember({ ...draftMember, username: e.target.value })} />
            <select value={draftMember.role} onChange={(e) => setDraftMember({ ...draftMember, role: e.target.value })}><option value="Member">Member</option><option value="Manager">Manager</option></select>
            <button onClick={addMember} type="button">추가</button>
          </div>
          {members.length === 0 ? <p className="pn-sub">아직 추가된 멤버가 없습니다.</p> : <ul>{members.map((m, i) => <li key={`${m.username}-${i}`}>{m.username} ({m.role})</li>)}</ul>}
        </section>

        <div className="pn-inline" style={{ justifyContent: 'flex-end', marginBottom: 0 }}>
          <Link className="pn-side-list" to="/projects">취소</Link>
          <button type="submit">프로젝트 생성</button>
        </div>
      </form>
    </UserLayout>
  );
}

export function ProjectDetailPage() {
  const { id } = useParams();
  const [project, setProject] = useState(null);
  const [form, setForm] = useState(null);
  const [coverForm, setCoverForm] = useState(null);
  const [editing, setEditing] = useState(false);
  const [error, setError] = useState('');
  const [msg, setMsg] = useState('');
  const [coverMsg, setCoverMsg] = useState('');

  useEffect(() => {
    async function load() {
      try {
        const rows = await apiFetch('/api/v1/projects');
        const found = Array.isArray(rows) ? rows.find((r) => String(r.id) === String(id)) : null;
        setProject(found || null);
        setForm(found || null);
        if (found) saveSelectedProject(found);
        if (!found) return;
        const cover = await apiFetch(`/api/v1/projects/${id}/cover`);
        setCoverForm(cover);
      } catch (e) {
        setError(e.message);
      }
    }
    load();
  }, [id]);

  async function saveProject(e) {
    e.preventDefault();
    setError('');
    setMsg('');
    try {
      const updated = await apiFetch(`/api/v1/projects/${id}/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': getCookie('csrftoken') },
        body: formEncoded(form || {})
      });
      setProject(updated);
      setForm(updated);
      saveSelectedProject(updated);
      setEditing(false);
      setMsg('프로젝트 정보를 수정했습니다.');
    } catch (e2) {
      setError(e2.message);
    }
  }

  async function onCoverFileChange(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    const asDataUrl = await new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result || ''));
      reader.onerror = () => reject(new Error('표지 파일을 읽지 못했습니다.'));
      reader.readAsDataURL(file);
    });
    setCoverForm((prev) => ({ ...(prev || {}), cover_image_data_url: asDataUrl }));
  }

  async function saveCover(e) {
    e.preventDefault();
    setError('');
    setCoverMsg('');
    try {
      const response = await apiFetch(`/api/v1/projects/${id}/cover`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': getCookie('csrftoken') },
        body: formEncoded(coverForm || {})
      });
      setCoverMsg(response?.message || '표지 설정을 저장했습니다.');
    } catch (e2) {
      setError(e2.message);
    }
  }

  function printCoverPdf() {
    window.location.href = `/api/v1/projects/${id}/cover/print`;
  }

  const coverPeriodText = [coverForm?.start_date || '', coverForm?.end_date || ''].filter(Boolean).join(' ~ ') || '-';
  const coverImagePreview = (coverForm?.cover_image_data_url || '').startsWith('data:image/');
  const hasPdfAsset = (coverForm?.cover_image_data_url || '').startsWith('data:application/pdf');

  return (
    <UserLayout title="프로젝트 상세">
      <ApiError error={error} />
      {msg && <p className="pn-sub">{msg}</p>}
      <section className="pn-card">
        {!project && <p className="pn-sub">프로젝트를 찾을 수 없습니다.</p>}
        {project && !editing && (
          <>
            <table className="pn-table"><tbody>
              <tr><th>ID</th><td>{project.id}</td></tr>
              <tr><th>이름</th><td>{project.name}</td></tr>
              <tr><th>코드</th><td>{project.code}</td></tr>
              <tr><th>상태</th><td>{project.status}</td></tr>
              <tr><th>매니저</th><td>{project.manager}</td></tr>
              <tr><th>기관</th><td>{project.organization || '-'}</td></tr>
              <tr><th>설명</th><td>{project.description || '-'}</td></tr>
              <tr><th>기간</th><td>{project.start_date || '-'} ~ {project.end_date || '-'}</td></tr>
            </tbody></table>
            <div className="pn-inline" style={{ justifyContent: 'flex-end' }}>
              <button className="pn-btn-secondary" onClick={printCoverPdf} type="button">표지 PDF 출력</button>
              <button onClick={() => setEditing(true)} type="button">수정하기</button>
            </div>
          </>
        )}
        {project && editing && form && (
          <form className="pn-grid2" onSubmit={saveProject}>
            <div><label className="pn-sub">과제명</label><input required value={form.name || ''} onChange={(e) => setForm({ ...form, name: e.target.value })} /></div>
            <div><label className="pn-sub">과제 책임자</label><input value={form.manager || ''} onChange={(e) => setForm({ ...form, manager: e.target.value })} /></div>
            <div><label className="pn-sub">사업명</label><input value={form.business_name || ''} onChange={(e) => setForm({ ...form, business_name: e.target.value })} /></div>
            <div><label className="pn-sub">기관</label><input value={form.organization || ''} onChange={(e) => setForm({ ...form, organization: e.target.value })} /></div>
            <div><label className="pn-sub">과제 번호</label><input value={form.code || ''} onChange={(e) => setForm({ ...form, code: e.target.value })} /></div>
            <div><label className="pn-sub">상태</label><select value={form.status || 'draft'} onChange={(e) => setForm({ ...form, status: e.target.value })}><option value="draft">draft</option><option value="active">active</option><option value="completed">completed</option></select></div>
            <div><label className="pn-sub">시작일</label><input type="date" value={form.start_date || ''} onChange={(e) => setForm({ ...form, start_date: e.target.value })} /></div>
            <div><label className="pn-sub">종료일</label><input type="date" value={form.end_date || ''} onChange={(e) => setForm({ ...form, end_date: e.target.value })} /></div>
            <div style={{ gridColumn: '1 / -1' }}><label className="pn-sub">설명</label><input value={form.description || ''} onChange={(e) => setForm({ ...form, description: e.target.value })} /></div>
            <div className="pn-inline" style={{ gridColumn: '1 / -1', justifyContent: 'flex-end' }}>
              <button className="pn-btn-secondary" onClick={() => { setEditing(false); setForm(project); }} type="button">취소</button>
              <button type="submit">저장</button>
            </div>
          </form>
        )}
      </section>

      {project && coverForm && (
        <section className="pn-card">
          <details open>
            <summary>표지 설정</summary>
            {coverMsg && <p className="pn-sub">{coverMsg}</p>}
            <div className="pn-cover-layout">
              <form className="pn-grid2" onSubmit={saveCover}>
                <div><label className="pn-sub">제목</label><input value={coverForm.title || ''} onChange={(e) => setCoverForm({ ...coverForm, title: e.target.value })} /></div>
                <div><label className="pn-sub">과제 번호</label><input value={coverForm.code || ''} onChange={(e) => setCoverForm({ ...coverForm, code: e.target.value })} /></div>
                <div><label className="pn-sub">사업명</label><input value={coverForm.business_name || ''} onChange={(e) => setCoverForm({ ...coverForm, business_name: e.target.value })} /></div>
                <div><label className="pn-sub">기관</label><input value={coverForm.organization || ''} onChange={(e) => setCoverForm({ ...coverForm, organization: e.target.value })} /></div>
                <div><label className="pn-sub">책임자</label><input value={coverForm.manager || ''} onChange={(e) => setCoverForm({ ...coverForm, manager: e.target.value })} /></div>
                <div><label className="pn-sub">시작일</label><input type="date" value={coverForm.start_date || ''} onChange={(e) => setCoverForm({ ...coverForm, start_date: e.target.value })} /></div>
                <div><label className="pn-sub">종료일</label><input type="date" value={coverForm.end_date || ''} onChange={(e) => setCoverForm({ ...coverForm, end_date: e.target.value })} /></div>
                <div style={{ gridColumn: '1 / -1' }}>
                  <label className="pn-sub">표시 옵션</label>
                  <div className="pn-cover-checks">
                    <label><input type="checkbox" checked={!!coverForm.show_title} onChange={(e) => setCoverForm({ ...coverForm, show_title: e.target.checked })} /> 제목</label>
                    <label><input type="checkbox" checked={!!coverForm.show_business_name} onChange={(e) => setCoverForm({ ...coverForm, show_business_name: e.target.checked })} /> 사업명</label>
                    <label><input type="checkbox" checked={!!coverForm.show_code} onChange={(e) => setCoverForm({ ...coverForm, show_code: e.target.checked })} /> 과제 번호</label>
                    <label><input type="checkbox" checked={!!coverForm.show_org} onChange={(e) => setCoverForm({ ...coverForm, show_org: e.target.checked })} /> 기관</label>
                    <label><input type="checkbox" checked={!!coverForm.show_manager} onChange={(e) => setCoverForm({ ...coverForm, show_manager: e.target.checked })} /> 책임자</label>
                    <label><input type="checkbox" checked={!!coverForm.show_period} onChange={(e) => setCoverForm({ ...coverForm, show_period: e.target.checked })} /> 기간</label>
                  </div>
                </div>
                <div style={{ gridColumn: '1 / -1' }}>
                  <label className="pn-sub">표지 원본 업로드 (이미지/PDF)</label>
                  <input type="file" accept="image/*,application/pdf" onChange={onCoverFileChange} />
                  {hasPdfAsset && <p className="pn-sub" style={{ marginTop: 6 }}>PDF 원본이 업로드되어 있습니다. 미리보기는 PDF 출력에서 확인할 수 있습니다.</p>}
                </div>
                <div className="pn-inline" style={{ gridColumn: '1 / -1', justifyContent: 'flex-end' }}>
                  <button className="pn-btn-secondary" onClick={printCoverPdf} type="button">표지 PDF 출력</button>
                  <button type="submit">표지 저장</button>
                </div>
              </form>

              <div className="pn-cover-preview-wrap">
                <div className={`pn-cover-a4${coverImagePreview ? ' has-bg' : ''}`}>
                  {coverImagePreview && <img className="pn-cover-bg" src={coverForm.cover_image_data_url} alt="cover" />}
                  <div className="pn-cover-head">Electronic Lab Notebook</div>
                  {coverForm.show_title && <h2 className="pn-cover-title">{coverForm.title || '-'}</h2>}
                  <table className="pn-cover-table">
                    <tbody>
                      {coverForm.show_code && <tr><th>과제 번호</th><td>{coverForm.code || '-'}</td></tr>}
                      {coverForm.show_business_name && <tr><th>사업명</th><td>{coverForm.business_name || '-'}</td></tr>}
                      {coverForm.show_org && <tr><th>기관명</th><td>{coverForm.organization || '-'}</td></tr>}
                      {coverForm.show_manager && <tr><th>책임자</th><td>{coverForm.manager || '-'}</td></tr>}
                      {coverForm.show_period && <tr><th>기간</th><td>{coverPeriodText}</td></tr>}
                    </tbody>
                  </table>
                  <div className="pn-cover-foot">ProjectNote</div>
                </div>
              </div>
            </div>
          </details>
        </section>
      )}
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
  const [rows, setRows] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [selectedUserId, setSelectedUserId] = useState('');
  const [error, setError] = useState('');
  const [msg, setMsg] = useState('');

  const load = useCallback(async () => {
    try {
      const [projectMembers, allResearchers] = await Promise.all([
        apiFetch(`/api/v1/projects/${id}/researchers`),
        apiFetch('/api/v1/researchers')
      ]);
      const members = Array.isArray(projectMembers) ? projectMembers : [];
      setRows(members);
      const memberIds = new Set(members.map((m) => String(m.id)));
      const all = Array.isArray(allResearchers) ? allResearchers : [];
      const available = all.filter((r) => !memberIds.has(String(r.id)));
      setCandidates(available);
      if (available.length > 0 && !selectedUserId) setSelectedUserId(String(available[0].id));
    } catch (e) {
      setError(e.message);
    }
  }, [id, selectedUserId]);

  useEffect(() => {
    load();
  }, [load]);


  async function addResearcher() {
    if (!selectedUserId) return;
    setError('');
    setMsg('');
    try {
      const res = await apiFetch(`/api/v1/projects/${id}/researchers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': getCookie('csrftoken') },
        body: formEncoded({ user_id: selectedUserId })
      });
      setMsg(res?.message || '연구원이 추가되었습니다.');
      await load();
    } catch (e) {
      setError(e.message);
    }
  }

  async function removeResearcher(userId) {
    setError('');
    setMsg('');
    try {
      const res = await apiFetch(`/api/v1/projects/${id}/researchers/remove`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': getCookie('csrftoken') },
        body: formEncoded({ user_id: userId })
      });
      setMsg(res?.message || '연구원을 제외했습니다.');
      await load();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <UserLayout title="참여 연구원 관리">
      <section className="pn-card">
        <p className="pn-sub" style={{ margin: 0 }}>프로젝트 #{id} 참여 연구원을 관리합니다.</p>
      </section>
      <section className="pn-card">
        <ApiError error={error} />
        {msg && <p className="pn-sub">{msg}</p>}
        <div className="pn-inline">
          <select value={selectedUserId} onChange={(e) => setSelectedUserId(e.target.value)}>
            {candidates.map((c) => <option key={c.id} value={c.id}>{c.name} ({c.username})</option>)}
            {candidates.length === 0 && <option value="">추가 가능한 연구원이 없습니다.</option>}
          </select>
          <button disabled={!selectedUserId} onClick={addResearcher} type="button">프로젝트에 추가</button>
        </div>
        <table className="pn-table">
          <thead><tr><th>이름</th><th>아이디</th><th>권한</th><th>이메일</th><th>기관</th><th>상태</th><th>관리</th></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td>{r.name}</td><td>{r.username}</td><td>{r.role}</td><td>{r.email}</td><td>{r.organization}</td><td>{r.status}</td>
                <td><button className="pn-danger" onClick={() => removeResearcher(r.id)} type="button">프로젝트 제외</button></td>
              </tr>
            ))}
            {rows.length === 0 && <tr><td colSpan={7} className="pn-sub">참여 연구원이 없습니다.</td></tr>}
          </tbody>
        </table>
      </section>
    </UserLayout>
  );
}

function ResearchersPageTable({ projectId = "" }) {
  const [rows, setRows] = useState([]);
  const [error, setError] = useState('');
  const [msg, setMsg] = useState('');
  const [form, setForm] = useState({ name: '', email: '', organization: '' });
  const [roleByUser, setRoleByUser] = useState({});

  const loadResearchers = useCallback(async () => {
    try {
      const endpoint = projectId ? `/api/v1/projects/${projectId}/researchers` : '/api/v1/researchers';
      const r = await apiFetch(endpoint);
      const list = Array.isArray(r) ? r : [];
      setRows(list);
      setRoleByUser(Object.fromEntries(list.map((u) => [u.id, u.role === '관리자' ? 'admin' : 'member'])));
    } catch (e) {
      setError(e.message);
    }
  }, [projectId]);

  useEffect(() => {
    loadResearchers();
  }, [loadResearchers]);

  async function createResearcher(e) {
    e.preventDefault();
    setError('');
    setMsg('');
    try {
      await apiFetch('/api/v1/researchers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': getCookie('csrftoken') },
        body: formEncoded({ action: 'create', ...form })
      });
      setMsg('연구원을 추가했습니다.');
      setForm({ name: '', email: '', organization: '' });
      loadResearchers();
    } catch (e2) {
      setError(e2.message);
    }
  }

  async function manageResearcher(userId, action, extra = {}) {
    setError('');
    setMsg('');
    try {
      await apiFetch('/api/v1/researchers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': getCookie('csrftoken') },
        body: formEncoded({ action, user_id: userId, ...extra })
      });
      setMsg('연구원 관리 작업이 반영되었습니다.');
      loadResearchers();
    } catch (e2) {
      setError(e2.message);
    }
  }

  return (
    <>
      {!projectId && <section className="pn-card">
        <h3>연구원 추가</h3>
        <form className="pn-grid" onSubmit={createResearcher} style={{ gap: 8 }}>
          <input placeholder="이름" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <input placeholder="이메일" required type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <input placeholder="소속/기관" required value={form.organization} onChange={(e) => setForm({ ...form, organization: e.target.value })} />
          <button type="submit">연구원 추가</button>
        </form>
      </section>}

      <section className="pn-card">
        <ApiError error={error} />
        {msg && <p className="pn-sub">{msg}</p>}
        <table className="pn-table">
          <thead><tr><th>이름</th><th>아이디</th><th>권한</th><th>이메일</th><th>기관</th><th>상태</th>{!projectId && <th>관리</th>}</tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td>{r.name}</td>
                <td>{r.username}</td>
                <td>{r.role}</td>
                <td>{r.email}</td>
                <td>{r.organization}</td>
                <td>{r.status}</td>
{!projectId && <td>
                  <div className="pn-inline" style={{ flexWrap: 'wrap', margin: 0 }}>
                    <button type="button" onClick={() => manageResearcher(r.id, 'approve')} disabled={Boolean(r.is_approved)}>승인</button>
                    <select value={roleByUser[r.id] || 'member'} onChange={(e) => setRoleByUser({ ...roleByUser, [r.id]: e.target.value })}>
                      <option value="member">일반</option>
                      <option value="admin">관리자</option>
                    </select>
                    <button type="button" onClick={() => manageResearcher(r.id, 'grant_role', { role: roleByUser[r.id] || 'member' })}>권한부여</button>
                    <button className="pn-danger" type="button" onClick={() => manageResearcher(r.id, 'expel')}>내보내기</button>
                  </div>
                </td>}
              </tr>
            ))}
            {rows.length === 0 && <tr><td className="pn-sub" colSpan={projectId ? 6 : 7}>연구원이 없습니다.</td></tr>}
          </tbody>
        </table>
      </section>
    </>
  );
}

function NotesTable({ endpoint }) {
  const [rows, setRows] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    apiFetch(endpoint)
      .then((r) => setRows(Array.isArray(r) ? r : []))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [endpoint]);

  return (
    <section className="pn-card">
      <Loading loading={loading} />
      <ApiError error={error} />
      <table className="pn-table">
        <thead><tr><th>제목</th><th>작성자</th><th>프로젝트 코드</th><th>기간</th><th>파일수</th><th>관리</th></tr></thead>
        <tbody>
          {rows.map((n) => (
            <tr key={n.id}>
              <td><Link className="pn-link" to={`/research-notes/${n.id}`}>{n.title}</Link></td>
              <td>{n.owner}</td>
              <td>{n.project_code}</td>
              <td>{n.period}</td>
              <td>{n.files}</td>
              <td>
                <div className="pn-inline" style={{ margin: 0 }}>
                  <Link className="pn-side-list" to={`/research-notes/${n.id}/viewer`}>뷰어</Link>
                  <Link className="pn-side-list" to={`/research-notes/${n.id}/cover`}>커버</Link>
                  <Link className="pn-side-list" to={`/research-notes/${n.id}/printable`}>출력</Link>
                </div>
              </td>
            </tr>
          ))}
          {rows.length === 0 && !loading && <tr><td colSpan={6} className="pn-sub">연구노트가 없습니다.</td></tr>}
        </tbody>
      </table>
    </section>
  );
}

export function ProjectResearchNotesPage() {
  const { id } = useParams();
  const nav = useNavigate();
  const [project, setProject] = useState(null);
  const [rows, setRows] = useState([]);
  const [uploadMeta, setUploadMeta] = useState({ title: '', summary: '', author: '' });
  const [error, setError] = useState('');
  const [msg, setMsg] = useState('');
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const projects = await apiFetch('/api/v1/projects');
      const found = Array.isArray(projects) ? projects.find((r) => String(r.id) === String(id)) : null;
      setProject(found || null);
      const notes = await apiFetch('/api/v1/research-notes');
      const filtered = Array.isArray(notes)
        ? notes.filter((n) => String(n.project_code || '') === String(found?.code || ''))
        : [];
      setRows(filtered);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  async function uploadProjectNoteFiles(fileList) {
    const files = Array.from(fileList || []);
    if (files.length === 0) return;
    setUploading(true);
    setError('');
    setMsg('');

    const allowed = ['jpeg', 'jpg', 'png', 'svg', 'tiff', 'webp', 'heif', 'heic', 'pdf'];
    const invalid = files.find((f) => !allowed.includes(String(f.name.split('.').pop() || '').toLowerCase()));
    if (invalid) {
      setUploading(false);
      setError('PDF 또는 이미지 파일만 업로드할 수 있습니다.');
      return;
    }

    try {
      let latestNoteId = '';
      for (const file of files) {
        const fd = new FormData();
        fd.append('research_note_file', file);
        if (uploadMeta.title.trim()) fd.append('title', uploadMeta.title.trim());
        if (uploadMeta.summary.trim()) fd.append('summary', uploadMeta.summary.trim());
        if (uploadMeta.author.trim()) fd.append('author', uploadMeta.author.trim());
        const res = await apiFetch(`/api/v1/projects/${id}/research-notes/upload`, {
          method: 'POST',
          headers: { 'X-CSRFToken': getCookie('csrftoken') },
          body: fd
        });
        latestNoteId = res?.note_id || latestNoteId;
      }
      setMsg(`${files.length}개 파일을 업로드해 연구노트를 생성했습니다.`);
      await load();
      if (latestNoteId) nav(`/research-notes/${latestNoteId}/viewer`);
    } catch (e) {
      setError(e.message);
    } finally {
      setUploading(false);
    }
  }

  return (
    <UserLayout title="연구노트 관리">
      <section className="pn-card">
        <h3>{project?.name || `프로젝트 #${id}`}</h3>
        <p className="pn-sub" style={{ margin: 0 }}>프로젝트 연구노트 목록입니다. 노트를 클릭하면 PDF 편집기로 이동합니다.</p>
      </section>

      <section className="pn-card">
        <h3 style={{ marginTop: 0 }}>업데이트 연구노트</h3>
        <div className="pn-grid2" style={{ marginBottom: 10 }}>
          <div><label className="pn-sub">제목(선택)</label><input value={uploadMeta.title} onChange={(e) => setUploadMeta((prev) => ({ ...prev, title: e.target.value }))} placeholder="업로드 파일명으로 자동 생성" /></div>
          <div><label className="pn-sub">작성자(선택)</label><input value={uploadMeta.author} onChange={(e) => setUploadMeta((prev) => ({ ...prev, author: e.target.value }))} placeholder="로그인 사용자" /></div>
          <div style={{ gridColumn: '1 / -1' }}><label className="pn-sub">요약(선택)</label><input value={uploadMeta.summary} onChange={(e) => setUploadMeta((prev) => ({ ...prev, summary: e.target.value }))} placeholder="업로드 시 연구노트 요약에 반영" /></div>
        </div>

        <input id="projectNoteUploadInput" type="file" accept=".pdf,image/*" multiple style={{ display: 'none' }} onChange={(e) => uploadProjectNoteFiles(e.target.files)} />
        <div
          className={`pn-note-dropzone ${dragActive ? 'drag' : ''}`}
          onDragEnter={(e) => { e.preventDefault(); setDragActive(true); }}
          onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
          onDragLeave={(e) => { e.preventDefault(); setDragActive(false); }}
          onDrop={(e) => { e.preventDefault(); setDragActive(false); uploadProjectNoteFiles(e.dataTransfer.files); }}
        >
          마우스로 드래그해서 연구파일(PDF/이미지)을 추가해주세요.
          <div className="pn-sub" style={{ marginTop: 8 }}>지원 파일 유형: PDF, JPEG, JPG, PNG, SVG, TIFF, WEBP, HEIF, HEIC</div>
          <div className="pn-inline" style={{ justifyContent: 'center', marginBottom: 0 }}>
            <label className="pn-side-list" htmlFor="projectNoteUploadInput" style={{ cursor: uploading ? 'not-allowed' : 'pointer', opacity: uploading ? .6 : 1 }}>
              {uploading ? '업로드 중...' : '파일 선택 업로드'}
            </label>
          </div>
        </div>
      </section>

      <section className="pn-card">
        <Loading loading={loading} />
        <ApiError error={error} />
        {msg && <p className="pn-sub">{msg}</p>}
        <table className="pn-table">
          <thead><tr><th>제목</th><th>작성자</th><th>프로젝트 코드</th><th>기간</th><th>파일수</th><th>관리</th></tr></thead>
          <tbody>
            {rows.map((n) => (
              <tr key={n.id}>
                <td><Link className="pn-link" to={`/research-notes/${n.id}/viewer`}>{n.title}</Link></td>
                <td>{n.owner}</td>
                <td>{n.project_code}</td>
                <td>{n.period}</td>
                <td>{n.files}</td>
                <td><button type="button" onClick={() => nav(`/research-notes/${n.id}/viewer`)}>PDF 편집기</button></td>
              </tr>
            ))}
            {rows.length === 0 && !loading && <tr><td colSpan={6} className="pn-sub">해당 프로젝트 연구노트가 없습니다. 위 업로드로 생성하세요.</td></tr>}
          </tbody>
        </table>
      </section>

    </UserLayout>
  );
}
export function ProjectResearchNotesPrintPage() { return <UserLayout title="프로젝트 연구노트 인쇄"><NotesTable endpoint="/api/v1/research-notes" /></UserLayout>; }
function ResearchNoteWorkspace({ id, mode }) {
  const nav = useNavigate();
  const [note, setNote] = useState(null);
  const [files, setFiles] = useState([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [signature, setSignature] = useState(null);
  const [error, setError] = useState('');
  const [previewUrl, setPreviewUrl] = useState('');
  const [previewError, setPreviewError] = useState('');
  const [loading, setLoading] = useState(true);

  const modeTitle = mode === 'viewer'
    ? '연구노트 뷰어'
    : mode === 'cover'
      ? '연구노트 표지'
      : mode === 'printable'
        ? '연구노트 출력'
        : '연구노트 상세';

  useEffect(() => {
    let canceled = false;
    async function load() {
      setLoading(true);
      setError('');
      try {
        const [detail, fileRows, sign] = await Promise.all([
          apiFetch(`/api/v1/research-notes/${id}`),
          apiFetch(`/api/v1/research-notes/${id}/files`),
          apiFetch('/api/v1/signatures').catch(() => null)
        ]);
        if (canceled) return;
        const list = Array.isArray(fileRows) ? fileRows : [];
        setNote(detail);
        setFiles(list);
        setSignature(sign);
        setSelectedIndex(0);
      } catch (e) {
        if (!canceled) setError(e.message);
      } finally {
        if (!canceled) setLoading(false);
      }
    }
    load();
    return () => { canceled = true; };
  }, [id]);

  const selectedFile = files[selectedIndex] || null;
  const canPrev = selectedIndex > 0;
  const canNext = selectedIndex < files.length - 1;
  const isImageFormat = useMemo(() => {
    const format = String(selectedFile?.format || '').toLowerCase();
    return ['jpeg', 'jpg', 'png', 'svg', 'tiff', 'webp', 'heif', 'heic', 'gif', 'bmp'].includes(format);
  }, [selectedFile?.format]);

  useEffect(() => {
    let canceled = false;
    let objectUrl = '';

    async function loadPreview() {
      setPreviewError('');
      setPreviewUrl('');
      if (!selectedFile?.content_url) return;
      try {
        const res = await fetch(selectedFile.content_url, { credentials: 'include' });
        if (!res.ok) throw new Error(`미리보기 로드 실패 (${res.status})`);
        const blob = await res.blob();
        if (canceled) return;
        objectUrl = window.URL.createObjectURL(blob);
        setPreviewUrl(objectUrl);
      } catch (_e) {
        if (!canceled) setPreviewError('브라우저 미리보기를 불러오지 못했습니다. 새 탭에서 열어주세요.');
      }
    }

    loadPreview();
    return () => {
      canceled = true;
      if (objectUrl) window.URL.revokeObjectURL(objectUrl);
    };
  }, [selectedFile?.id, selectedFile?.content_url]);

  return (
    <UserLayout title={modeTitle}>
      <Loading loading={loading} />
      <ApiError error={error} />

      <section className="pn-card">
        <div className="pn-inline" style={{ justifyContent: 'space-between', margin: 0, flexWrap: 'wrap' }}>
          <div>
            <h3 style={{ marginBottom: 0 }}>{note?.title || `연구노트 #${id}`}</h3>
            <p className="pn-sub" style={{ marginBottom: 0 }}>A4 형태 연구노트</p>
          </div>
          <div className="pn-inline" style={{ margin: 0 }}>
            <button className="pn-btn-secondary" onClick={() => nav(-1)} type="button">돌아가기</button>
            <button className="pn-btn-secondary" disabled={!canPrev} onClick={() => setSelectedIndex((i) => Math.max(0, i - 1))} type="button">이전 연구노트</button>
            <button disabled={!canNext} onClick={() => setSelectedIndex((i) => Math.min(files.length - 1, i + 1))} type="button">다음 연구노트</button>
          </div>
        </div>
      </section>

      <section className="pn-card" style={{ marginTop: 12 }}>
        {selectedFile ? (
          <div className="pn-note-paper-wrap">
            <article className="pn-note-paper">
              <header className="pn-note-paper-header">
                <h4>{note?.title || selectedFile.name}</h4>
              </header>

              <main className="pn-note-paper-content">
                {previewError && <p className="pn-sub">{previewError}</p>}
                {previewUrl && isImageFormat && <img alt={selectedFile.name} className="pn-note-paper-image" src={previewUrl} />}
                {previewUrl && !isImageFormat && <iframe src={previewUrl} style={{ width: '100%', minHeight: 720, border: 0 }} title={`preview-${selectedFile.id}`} />}
                {!previewUrl && !previewError && <p className="pn-sub">미리보기를 준비중입니다...</p>}
              </main>

              <footer className="pn-note-paper-footer">
                <div>
                  <span className="pn-sub">작성자</span>
                  <strong>{selectedFile.author || note?.owner || '-'}</strong>
                </div>
                <div>
                  <span className="pn-sub">사인</span>
                  {signature?.signature_data_url
                    ? <img alt="사인" className="pn-note-signature" src={signature.signature_data_url} />
                    : <span className="pn-sub">사인 없음</span>}
                </div>
                <div>
                  <span className="pn-sub">작성 일자</span>
                  <strong>{selectedFile.created || '-'}</strong>
                </div>
              </footer>
            </article>
          </div>
        ) : <p className="pn-sub">표시할 연구파일이 없습니다.</p>}
      </section>
    </UserLayout>
  );
}

export function ResearchNoteDetailPage() {
  const { id } = useParams();
  return <ResearchNoteWorkspace id={id} mode="detail" />;
}

export function ResearchNoteViewerPage() {
  const { id } = useParams();
  return <ResearchNoteWorkspace id={id} mode="viewer" />;
}

export function ResearchNoteCoverPage() {
  const { id } = useParams();
  return <ResearchNoteWorkspace id={id} mode="cover" />;
}

export function ResearchNotePrintablePage() {
  const { id } = useParams();
  return <ResearchNoteWorkspace id={id} mode="printable" />;
}

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
