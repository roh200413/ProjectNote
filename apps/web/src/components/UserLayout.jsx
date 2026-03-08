import { useEffect, useMemo, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { apiFetch } from '../utils/http';
import { clearSelectedProject, readSelectedProject, saveSelectedProject } from '../utils/projectContext';

const nav = [
  ['/', '🏠', '대시보드'],
  ['/researchers', '👥', '연구원 통합 관리'],
  ['/integrations/github', '🔗', '지허브 통합 관리'],
  ['/data-updates', '🤝', '협업 툴 통합 관리']
];

export default function UserLayout({ title, children }) {
  const [collapsed, setCollapsed] = useState(false);
  const [activeProject, setActiveProject] = useState(() => readSelectedProject());
  const [projectMenuOpen, setProjectMenuOpen] = useState(true);
  const location = useLocation();

  const projectId = useMemo(() => {
    const match = location.pathname.match(/^\/projects\/([^/]+)/);
    return match ? match[1] : '';
  }, [location.pathname]);

  useEffect(() => {
    if (!projectId) {
      setActiveProject(readSelectedProject());
      return;
    }

    let cancelled = false;
    apiFetch('/api/v1/projects')
      .then((rows) => {
        if (cancelled) return;
        const found = Array.isArray(rows) ? rows.find((r) => String(r.id) === String(projectId)) : null;
        const project = found || { id: projectId, name: `프로젝트 #${projectId}`, code: '-' };
        setActiveProject(project);
        saveSelectedProject(project);
      })
      .catch(() => {
        if (cancelled) return;
        const fallback = { id: projectId, name: `프로젝트 #${projectId}`, code: '-' };
        setActiveProject(fallback);
        saveSelectedProject(fallback);
      });

    return () => {
      cancelled = true;
    };
  }, [projectId]);

  useEffect(() => {
    if (activeProject?.id) setProjectMenuOpen(true);
  }, [activeProject?.id]);

  return (
    <div className={`pn-layout ${collapsed ? 'sidebar-collapsed' : ''}`}>
      <aside className="pn-sidebar">
        <div className="pn-side-head">
          <div className="pn-logo">Project Note</div>
          <button className="pn-collapse-btn" onClick={() => setCollapsed((v) => !v)} type="button">☰</button>
        </div>

        <nav className="pn-menu">
          {nav.map(([to, icon, label]) => (
            <Link className={`pn-side-link ${location.pathname === to ? 'active' : ''}`} key={to} to={to}>
              <span className="pn-side-icon">{icon}</span>
              <span className="pn-side-text">{label}</span>
            </Link>
          ))}
        </nav>

        {activeProject?.id && (
          <section className="pn-project-context">
            <button className="pn-project-context-toggle" onClick={() => setProjectMenuOpen((v) => !v)} type="button">
              <span>현재 프로젝트</span>
              <span aria-hidden="true">{projectMenuOpen ? '▾' : '▸'}</span>
            </button>
            <div className="pn-project-context-name">{activeProject.name}</div>
            <div className="pn-sub" style={{ margin: 0 }}>코드: {activeProject.code || '-'}</div>
            {projectMenuOpen && (
              <div className="pn-project-context-menu">
                <Link className={`pn-side-list ${location.pathname === `/projects/${activeProject.id}` ? 'active' : ''}`} to={`/projects/${activeProject.id}`}>
                  프로젝트 상세 보기 및 수정
                </Link>
                <Link className={`pn-side-list ${location.pathname === `/projects/${activeProject.id}/research-notes` ? 'active' : ''}`} to={`/projects/${activeProject.id}/research-notes`}>
                  연구노트 관리
                </Link>
                <Link className={`pn-side-list ${location.pathname === `/projects/${activeProject.id}/researchers` ? 'active' : ''}`} to={`/projects/${activeProject.id}/researchers`}>
                  참여 연구원 관리
                </Link>
                <button className="pn-side-list" onClick={() => { clearSelectedProject(); setActiveProject(null); }} style={{ textAlign: 'left', width: '100%', cursor: 'pointer' }} type="button">
                  프로젝트 메뉴 닫기
                </button>
              </div>
            )}
          </section>
        )}
      </aside>

      <section className="pn-main">
        <main className="pn-shell">
          <div className="pn-headline pn-headline-row">
            <div>
              <h1 className="pn-title">{title}</h1>
              <p className="pn-sub" style={{ margin: 0 }}>일반 사용자 화면 · React</p>
            </div>
            <div className="pn-top-actions" role="navigation">
              <Link className="pn-side-link" to="/my-page">
                <span className="pn-side-icon">👤</span>
                <span className="pn-side-text">개인 페이지</span>
              </Link>
              <Link className="pn-side-link" to="/logout">
                <span className="pn-side-icon">↪</span>
                <span className="pn-side-text">로그아웃</span>
              </Link>
            </div>
          </div>
          {children}
        </main>
      </section>
    </div>
  );
}
