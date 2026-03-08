import { useEffect, useState } from 'react';
import AdminLayout from '../components/AdminLayout';
import { apiFetch, formEncoded, getCookie } from '../utils/http';

export default function AdminTeamsPage() {
  const [teams, setTeams] = useState([]);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');
  const [toast, setToast] = useState('');

  const load = () => {
    apiFetch('/api/v1/admin/teams')
      .then((data) => setTeams(Array.isArray(data) ? data : []))
      .catch((e) => setError(e.message));
  };

  useEffect(() => {
    load();
  }, []);

  async function createTeam(e) {
    e.preventDefault();
    try {
      const created = await apiFetch('/api/v1/admin/teams', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': getCookie('csrftoken')
        },
        body: formEncoded({ name, description })
      });
      setToast(`팀 생성 완료: ${created.name} (코드 ${created.join_code})`);
      setName('');
      setDescription('');
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <AdminLayout active="teams" title="ADMIN · 팀 관리">
      <section className="pn-card">
        <h3 style={{ marginTop: 0 }}>팀 관리</h3>
        <form className="pn-grid" onSubmit={createTeam} style={{ gap: 8 }}>
          <div><label className="pn-sub">팀 이름</label><input onChange={(e) => setName(e.target.value)} required value={name} /></div>
          <div><label className="pn-sub">설명</label><input onChange={(e) => setDescription(e.target.value)} value={description} /></div>
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}><button type="submit">팀 생성</button></div>
        </form>

        {error && <p className="pn-err">{error}</p>}
        {toast && <p className="pn-sub">{toast}</p>}

        <h4 style={{ margin: '14px 0 8px' }}>팀 목록</h4>
        <table className="pn-table">
          <thead><tr><th>ID</th><th>팀 이름</th><th>팀 코드</th><th>설명</th></tr></thead>
          <tbody>
            {teams.length > 0 ? teams.map((t) => (
              <tr key={t.id}><td>{t.id}</td><td>{t.name}</td><td>{t.join_code}</td><td>{t.description || ''}</td></tr>
            )) : <tr><td className="pn-sub" colSpan={4}>생성된 팀이 없습니다.</td></tr>}
          </tbody>
        </table>
      </section>
    </AdminLayout>
  );
}
