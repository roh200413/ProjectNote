import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiFetch } from '../utils/http';

export default function AdminDashboardPage() {
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    apiFetch('/api/v1/dashboard/summary').then(setSummary).catch((e) => setError(e.message));
  }, []);

  return (
    <section className="pn-page">
      <h1>관리자 대시보드 (React)</h1>
      <nav className="pn-nav-links">
        <Link to="/admin/users">사용자</Link>
        <Link to="/admin/teams">팀</Link>
        <Link to="/admin/tables">테이블</Link>
      </nav>
      {error && <p className="pn-err">{error}</p>}
      {summary && (
        <div className="pn-grid3">
          <article className="pn-card"><h3>프로젝트</h3><p>{summary.projects}</p></article>
          <article className="pn-card"><h3>연구자</h3><p>{summary.researchers}</p></article>
          <article className="pn-card"><h3>노트</h3><p>{summary.notes}</p></article>
        </div>
      )}
    </section>
  );
}
