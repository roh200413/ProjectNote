import { useEffect, useState } from 'react';
import { apiFetch, getCookie } from '../utils/http';

export default function AdminTablesPage() {
  const [tables, setTables] = useState([]);
  const [error, setError] = useState('');

  const load = () => apiFetch('/api/v1/admin/tables').then((data) => setTables(Array.isArray(data) ? data : [])).catch((e) => setError(e.message));
  useEffect(() => { load(); }, []);

  async function truncate(tableName) {
    if (!window.confirm(`${tableName} 비우기?`)) return;
    try {
      await apiFetch(`/api/v1/admin/tables/${tableName}/truncate`, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
      });
      load();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <section className="pn-page">
      <h1>테이블 관리 (React)</h1>
      {error && <p className="pn-err">{error}</p>}
      <table className="pn-table">
        <thead><tr><th>테이블</th><th>건수</th><th>작업</th></tr></thead>
        <tbody>
          {tables.map((t) => <tr key={t.table}><td>{t.table}</td><td>{t.count}</td><td><button onClick={() => truncate(t.table)}>비우기</button></td></tr>)}
        </tbody>
      </table>
    </section>
  );
}
