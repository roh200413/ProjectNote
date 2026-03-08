import { useCallback, useEffect, useMemo, useState } from 'react';
import AdminLayout from '../components/AdminLayout';
import { apiFetch, formEncoded, getCookie } from '../utils/http';

export default function AdminUsersPage() {
  const [users, setUsers] = useState([]);
  const [teams, setTeams] = useState([]);
  const [keyword, setKeyword] = useState('');
  const [error, setError] = useState('');
  const [toast, setToast] = useState('');

  const load = useCallback(async () => {
    try {
      const [u, t] = await Promise.all([
        apiFetch(`/api/v1/admin/users${keyword ? `?q=${encodeURIComponent(keyword)}` : ''}`),
        apiFetch('/api/v1/admin/teams')
      ]);
      setUsers(Array.isArray(u) ? u : []);
      setTeams(Array.isArray(t) ? t : []);
      setError('');
    } catch (e) {
      setError(e.message);
    }
  }, [keyword]);

  useEffect(() => {
    load();
  }, [load]);

  const teamMap = useMemo(() => {
    const m = new Map();
    teams.forEach((t) => m.set(t.name, t.id));
    return m;
  }, [teams]);

  async function submitAction(payload, successMessage) {
    try {
      await apiFetch('/api/v1/admin/users', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': getCookie('csrftoken')
        },
        body: formEncoded(payload)
      });
      setToast(successMessage || '처리 완료');
      await load();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <AdminLayout active="users" title="ADMIN · 사용자 관리">
      <section className="pn-card">
        <h3 style={{ marginTop: 0 }}>가입자 승인/팀 할당/권한 부여</h3>
        <div className="pn-inline">
          <input onChange={(e) => setKeyword(e.target.value)} placeholder="검색" value={keyword} />
          <button onClick={load} type="button">검색</button>
        </div>
        {error && <p className="pn-err">{error}</p>}
        {toast && <p className="pn-sub">{toast}</p>}

        <table className="pn-table">
          <thead>
            <tr>
              <th>ID</th><th>아이디</th><th>이름</th><th>이메일</th><th>현재팀</th><th>현재권한</th><th>승인</th><th>관리</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>{u.id}</td>
                <td>{u.username}</td>
                <td>{u.display_name}</td>
                <td>{u.email}</td>
                <td>{u.team || '-'}</td>
                <td>{u.role}</td>
                <td>{u.is_approved ? '승인' : '대기'}</td>
                <td>
                  <div className="pn-inline" style={{ margin: 0, flexWrap: 'wrap' }}>
                    <select defaultValue="" id={`team-${u.id}`}>
                      <option value="">팀 선택</option>
                      {teams.map((t) => <option key={t.id} value={t.id}>{t.name} ({t.join_code})</option>)}
                    </select>
                    <button
                      onClick={() => {
                        const teamId = document.getElementById(`team-${u.id}`).value;
                        if (!teamId) return;
                        submitAction({ user_id: u.id, action: 'assign_team', team_id: teamId }, '팀 할당 완료');
                      }}
                      type="button"
                    >팀 할당</button>
                    {!u.is_approved && <button onClick={() => submitAction({ user_id: u.id, action: 'approve' }, '승인 완료')} type="button">승인</button>}
                    <button onClick={() => submitAction({ user_id: u.id, action: 'grant_role', role: 'admin' }, '권한 변경 완료')} type="button">관리자 권한</button>
                    <button onClick={() => submitAction({ user_id: u.id, action: 'grant_role', role: 'member' }, '권한 변경 완료')} type="button">일반 권한</button>
                    <button
                      className="pn-danger"
                      onClick={() => {
                        if (window.confirm('정말 해당 사용자를 내보내시겠습니까?')) {
                          submitAction({ user_id: u.id, action: 'expel' }, '내보내기 완료');
                        }
                      }}
                      type="button"
                    >내보내기</button>
                  </div>
                </td>
              </tr>
            ))}
            {users.length === 0 && (
              <tr><td className="pn-sub" colSpan={8}>등록된 사용자가 없습니다.</td></tr>
            )}
          </tbody>
        </table>
      </section>
    </AdminLayout>
  );
}
