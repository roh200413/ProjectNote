import { useEffect, useMemo, useState } from 'react';
import AdminLayout from '../components/AdminLayout';
import { apiFetch, formEncoded, getCookie } from '../utils/http';

function buildStats(teams, users) {
  return teams
    .map((team) => {
      const members = users.filter((u) => u.team === team.name && u.is_approved);
      const owner = members.find((m) => m.role === '소유자');
      return {
        teamId: team.id,
        teamName: team.name,
        joinCode: team.join_code,
        userCount: members.length,
        ownerName: owner?.display_name || '미지정',
        ownerUserId: owner?.id || '',
        members
      };
    })
    .sort((a, b) => b.userCount - a.userCount);
}

export default function AdminDashboardPage() {
  const [summary, setSummary] = useState(null);
  const [teams, setTeams] = useState([]);
  const [users, setUsers] = useState([]);
  const [error, setError] = useState('');
  const [toast, setToast] = useState('');

  const load = async () => {
    try {
      const [s, t, u] = await Promise.all([
        apiFetch('/api/v1/dashboard/summary'),
        apiFetch('/api/v1/admin/teams'),
        apiFetch('/api/v1/admin/users')
      ]);
      setSummary(s);
      setTeams(Array.isArray(t) ? t : []);
      setUsers(Array.isArray(u) ? u : []);
      setError('');
    } catch (e) {
      setError(e.message);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const orgStats = useMemo(() => buildStats(teams, users), [teams, users]);

  async function setOwner(teamId, ownerUserId) {
    if (!ownerUserId) return;
    try {
      await apiFetch('/api/v1/admin/users', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': getCookie('csrftoken')
        },
        body: formEncoded({ action: 'set_owner', team_id: teamId, owner_user_id: ownerUserId })
      });
      setToast('소유주 변경 완료');
      await load();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <AdminLayout active="dashboard" title="ADMIN 대시보드">
      {error && <p className="pn-err">{error}</p>}
      {toast && <p className="pn-sub">{toast}</p>}
      <section className="pn-grid3" style={{ marginBottom: 12 }}>
        <article className="pn-card"><div className="pn-sub">기관 수</div><h3>{summary?.teams ?? '-'}</h3></article>
        <article className="pn-card"><div className="pn-sub">사용자 수</div><h3>{summary?.researchers ?? '-'}</h3></article>
        <article className="pn-card"><div className="pn-sub">노트 수</div><h3>{summary?.notes ?? '-'}</h3></article>
      </section>

      <section className="pn-card" style={{ marginBottom: 12 }}>
        <h3 style={{ marginTop: 0 }}>기관별 사용자 현황</h3>
        <div className="pn-grid3">
          {orgStats.map((item) => (
            <article className="pn-card" key={item.teamId} style={{ padding: 14 }}>
              <h4 style={{ margin: '0 0 6px' }}>{item.teamName}</h4>
              <div className="pn-sub" style={{ marginBottom: 8 }}>팀 코드: {item.joinCode}</div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <span><strong>사용자 수</strong> {item.userCount}</span>
                <span><strong>소유자</strong> {item.ownerName}</span>
              </div>
              {item.members.length > 0 && (
                <div className="pn-inline">
                  <select defaultValue={item.ownerUserId || ''} id={`owner-${item.teamId}`}>
                    <option value="">선택</option>
                    {item.members.map((m) => (
                      <option key={m.id} value={m.id}>{m.display_name}</option>
                    ))}
                  </select>
                  <button
                    onClick={() => setOwner(item.teamId, document.getElementById(`owner-${item.teamId}`).value)}
                    type="button"
                  >
                    소유주 변경
                  </button>
                </div>
              )}
            </article>
          ))}
        </div>
      </section>

      <section className="pn-card">
        <h3 style={{ marginTop: 0 }}>권한 안내</h3>
        <p className="pn-sub" style={{ margin: 0 }}>
          슈퍼 어드민은 데이터 테이블 조회/초기화 관리만 가능합니다. 팀 관리 및 일반 가입자 관리는 일반 사용자 계정으로 로그인 후 진행하세요.
        </p>
      </section>
    </AdminLayout>
  );
}
