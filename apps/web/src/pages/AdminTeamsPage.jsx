import { useEffect, useState } from 'react';
import { apiFetch, formEncoded, getCookie } from '../utils/http';

export default function AdminTeamsPage() {
  const [teams, setTeams] = useState([]);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');

  const load = () => apiFetch('/api/v1/admin/teams').then((data) => setTeams(Array.isArray(data) ? data : [])).catch((e) => setError(e.message));
  useEffect(() => { load(); }, []);

  async function createTeam(e) {
    e.preventDefault();
    setError('');
    try {
      await apiFetch('/api/v1/admin/teams', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': getCookie('csrftoken')
        },
        body: formEncoded({ name, description })
      });
      setName('');
      setDescription('');
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section className="pn-page">
      <h1>팀 관리 (React)</h1>
      {error && <p className="pn-err">{error}</p>}
      <form className="pn-inline" onSubmit={createTeam}>
        <input onChange={(e) => setName(e.target.value)} placeholder="팀 이름" value={name} />
        <input onChange={(e) => setDescription(e.target.value)} placeholder="설명" value={description} />
        <button type="submit">팀 생성</button>
      </form>
      <table className="pn-table">
        <thead><tr><th>ID</th><th>이름</th><th>설명</th><th>코드</th></tr></thead>
        <tbody>
          {teams.map((t) => <tr key={t.id}><td>{t.id}</td><td>{t.name}</td><td>{t.description}</td><td>{t.join_code}</td></tr>)}
        </tbody>
      </table>
    </section>
  );
}
