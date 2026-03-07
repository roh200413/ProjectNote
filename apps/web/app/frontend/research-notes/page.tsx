'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';

type SessionUser = {
  name?: string;
  username?: string;
  role?: string;
};

type NoteRow = {
  id: string;
  title: string;
  owner: string;
  project_code: string;
  period: string;
  files: number;
  members: number;
};

const PAGE_SIZE = 10;

function normalizeRole(role?: string): string {
  if (!role) return '미인증';
  if (role === 'owner') return '소유자';
  if (role === 'admin') return '관리자';
  if (role === 'member') return '일반';
  return role;
}

export default function FrontendResearchNotesPage() {
  const [notes, setNotes] = useState<NoteRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [user, setUser] = useState<SessionUser | null>(null);

  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);

  useEffect(() => {
    const run = async () => {
      setLoading(true);
      setError('');
      try {
        const [notesRes, meRes] = await Promise.all([
          fetch('/api/research-notes', { cache: 'no-store' }),
          fetch('/api/auth/me', { cache: 'no-store' }),
        ]);

        const notesBody = (await notesRes.json().catch(() => [])) as NoteRow[];
        if (!notesRes.ok) throw new Error('연구노트 목록을 불러오지 못했습니다.');
        setNotes(Array.isArray(notesBody) ? notesBody : []);

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
    if (!q) return notes;
    return notes.filter((item) =>
      [item.title, item.owner, item.project_code, item.id].some((v) =>
        String(v).toLowerCase().includes(q),
      ),
    );
  }, [notes, query]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages);
  const paged = filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);

  useEffect(() => {
    setPage(1);
  }, [query]);

  return (
    <main className="list-main">
      <section className="list-card">
        <div className="list-header-row">
          <div>
            <span className="badge">화면 이관 1차 · /frontend/research-notes</span>
            <h1>연구노트 목록 (Web)</h1>
            <p className="muted">기존 조회 중심 화면을 테이블/검색 기반으로 이관했습니다.</p>
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
            placeholder="제목/책임자/과제번호/ID 검색"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <Link href="/frontend/projects" className="btn-link">프로젝트 화면으로</Link>
        </div>

        {loading && <p className="muted">불러오는 중...</p>}
        {error && <p className="err">{error}</p>}

        {!loading && !error && (
          <>
            <table className="table">
              <thead>
                <tr>
                  <th>제목</th>
                  <th>책임자</th>
                  <th>과제번호</th>
                  <th>기간</th>
                  <th>파일/연구원</th>
                  <th>액션</th>
                </tr>
              </thead>
              <tbody>
                {paged.map((row) => (
                  <tr key={row.id}>
                    <td>{row.title}</td>
                    <td>{row.owner}</td>
                    <td>{row.project_code || '-'}</td>
                    <td>{row.period || '-'}</td>
                    <td>{row.files} / {row.members}</td>
                    <td><Link href={`/frontend/research-notes/${row.id}/viewer`} className="btn-link">viewer</Link></td>
                  </tr>
                ))}
                {paged.length === 0 && (
                  <tr>
                    <td colSpan={6} className="muted">조건에 맞는 연구노트가 없습니다.</td>
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
