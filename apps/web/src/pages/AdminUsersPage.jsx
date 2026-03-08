import { useEffect, useState } from 'react';
import { apiFetch, formEncoded, getCookie } from '../utils/http';

export default function AdminUsersPage() {
  const [users, setUsers] = useState([]);
  const [teams, setTeams] = useState([]);
  const [error, setError] = useState('');

  const load = async () => {
    try {
      const [u, t] = await Promise.all([apiFetch('/api/v1/admin/users'), apiFetch('/api/v1/admin/teams')]);
      setUsers(Array.isArray(u) ? u : []);
      setTeams(Array.isArray(t) ? t : []);
    } catch (e) {
      setError(e.message);
    }
  };

  useEffect(() => { load(); }, []);

  async function updateUser(userId, action, extra = {}) {
    setError('');
    try {
      await apiFetch('/api/v1/admin/users', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': getCookie('csrftoken')
        },
        body: formEncoded({ user_id: userId, action, ...extra })
      });
      load();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <section className="pn-page">
      <h1>사용자 관리 (React)</h1>
      {error && <p className="pn-err">{error}</p>}
      <table className="pn-table">
        <thead><tr><th>사용자</th><th>팀</th><th>권한</th><th>승인</th><th>작업</th></tr></thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id}>
              <td>{u.display_name} ({u.username})</td>
              <td>{u.team}</td>
              <td>{u.role}</td>
              <td>{u.is_approved ? 'Y' : 'N'}</td>
              <td>
                <button onClick={() => updateUser(u.id, 'approve')}>승인</button>
                <button onClick={() => updateUser(u.id, 'grant_role', { role: 'member' })}>멤버화</button>
                <button onClick={() => updateUser(u.id, 'expel')}>삭제</button>
                <select onChange={(e) => e.target.value && updateUser(u.id, 'assign_team', { team_id: e.target.value })}>
                  <option value="">팀 지정</option>
                  {teams.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
                </select>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
