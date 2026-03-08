import { useEffect, useState } from 'react';
import AdminLayout from '../components/AdminLayout';
import { apiFetch, getCookie } from '../utils/http';

export default function AdminTablesPage() {
  const [tables, setTables] = useState([]);
  const [error, setError] = useState('');
  const [toast, setToast] = useState('');

  const load = () => {
    apiFetch('/api/v1/admin/tables')
      .then((data) => setTables(Array.isArray(data) ? data : []))
      .catch((e) => setError(e.message));
  };

  useEffect(() => {
    load();
  }, []);

  async function truncate(tableName) {
    if (!window.confirm(`${tableName} 테이블 데이터를 비우시겠습니까?`)) return;
    try {
      const result = await apiFetch(`/api/v1/admin/tables/${tableName}/truncate`, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
      });
      setToast(result?.message || '처리 완료');
      load();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <AdminLayout active="tables" title="ADMIN · 테이블 관리">
      <section className="pn-card">
        <h3 style={{ marginTop: 0 }}>테이블 관리</h3>
        <p className="pn-sub">테이블 데이터 건수 확인 및 비우기(truncate) 기능</p>
        {error && <p className="pn-err">{error}</p>}
        {toast && <p className="pn-sub">{toast}</p>}
        <table className="pn-table">
          <thead><tr><th>테이블</th><th>행 수</th><th>관리</th></tr></thead>
          <tbody>
            {tables.length > 0 ? tables.map((t) => (
              <tr key={t.table}>
                <td>{t.table}</td>
                <td>{t.rows}</td>
                <td><button onClick={() => truncate(t.table)} type="button">데이터 비우기</button></td>
              </tr>
            )) : <tr><td className="pn-sub" colSpan={3}>관리 대상 테이블이 없습니다.</td></tr>}
          </tbody>
        </table>
      </section>
    </AdminLayout>
  );
}
