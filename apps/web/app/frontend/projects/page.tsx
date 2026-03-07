'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';

type SessionUser = {
  name?: string;
  username?: string;
  role?: string;
};

type ProjectRow = {
  id: string;
  name: string;
  manager: string;
  organization?: string;
  status: string;
};

const PAGE_SIZE = 9;

function normalizeRole(role?: string): string {
  if (!role) return '미인증';
  if (role === 'owner') return '소유자';
  if (role === 'admin') return '관리자';
  if (role === 'member') return '일반';
  return role;
}

export default function FrontendProjectsPage() {
  const [projects, setProjects] = useState<ProjectRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [user, setUser] = useState<SessionUser | null>(null);

  const [query, setQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [page, setPage] = useState(1);

  useEffect(() => {
    const run = async () => {
      setLoading(true);
      setError('');
      try {
        const [projectsRes, meRes] = await Promise.all([
          fetch('/api/projects', { cache: 'no-store' }),
          fetch('/api/auth/me', { cache: 'no-store' }),
        ]);

        const projectsBody = (await projectsRes.json().catch(() => [])) as ProjectRow[];
        if (!projectsRes.ok) throw new Error('프로젝트 목록을 불러오지 못했습니다.');
        setProjects(Array.isArray(projectsBody) ? projectsBody : []);

        const meBody = (await meRes.json().catch(() => ({}))) as { user?: SessionUser };
        setUser(meRes.ok ? meBody.user || null : null);
      } catch (err) {
        setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.');
      } finally {
        setLoading(false);
      }
    };
    run();
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return projects.filter((item) => {
      const statusMatched = statusFilter === 'all' ? true : item.status === statusFilter;
      if (!statusMatched) return false;
      if (!q) return true;
      return [item.name, item.manager, item.organization || '', item.id].some((v) =>
        String(v).toLowerCase().includes(q),
      );
    });
  }, [projects, query, statusFilter]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages);
  const paged = filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);

  useEffect(() => {
    setPage(1);
  }, [query, statusFilter]);

  return (
    <main className="list-main">
      <section className="list-card">
        <div className="list-header-row">
          <div>
            <span className="badge">화면 이관 1차 · /frontend/projects</span>
            <h1>프로젝트 관리 (Web)</h1>
            <p className="muted">조회/리스트 중심 페이지를 우선 이관했습니다.</p>
          </div>
          <div className="role-box">
            <div>권한 표시</div>
            <strong>{normalizeRole(user?.role)}</strong>
            <small className="muted">{user?.name || user?.username || '로그인 사용자 정보 없음'}</small>
          </div>
        </div>

        <div className="toolbar">
          <input
            className="input"
            placeholder="프로젝트명/담당자/기관/ID 검색"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <select
            className="input"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as 'all' | 'active' | 'inactive')}
          >
            <option value="all">전체 상태</option>
            <option value="active">active</option>
            <option value="inactive">inactive</option>
          </select>
          <Link href="/frontend/research-notes" className="btn-link">연구노트 화면으로</Link>
        </div>

        {loading && <p className="muted">불러오는 중...</p>}
        {error && <p className="err">{error}</p>}

        {!loading && !error && (
          <>
            <table className="table">
              <thead>
                <tr>
                  <th>이름</th>
                  <th>담당자</th>
                  <th>기관</th>
                  <th>상태</th>
                  <th>ID</th>
                  <th>액션</th>
                </tr>
              </thead>
              <tbody>
                {paged.map((row) => (
                  <tr key={row.id}>
                    <td>{row.name}</td>
                    <td>{row.manager}</td>
                    <td>{row.organization || '미지정'}</td>
                    <td>{row.status}</td>
                    <td className="mono">{row.id}</td>
                    <td><Link href={`/frontend/projects/${row.id}/research-notes`} className="btn-link">고위험 작업</Link></td>
                  </tr>
                ))}
                {paged.length === 0 && (
                  <tr>
                    <td colSpan={6} className="muted">조건에 맞는 프로젝트가 없습니다.</td>
                  </tr>
                )}
              </tbody>
            </table>

            <div className="pager">
              <button className="btn" disabled={currentPage <= 1} onClick={() => setPage((p) => p - 1)}>
                이전
              </button>
              <span className="muted">{currentPage} / {totalPages} (총 {filtered.length}건)</span>
              <button className="btn" disabled={currentPage >= totalPages} onClick={() => setPage((p) => p + 1)}>
                다음
              </button>
            </div>
          </>
        )}
      </section>
    </main>
  );
}
