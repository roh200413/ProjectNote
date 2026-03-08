import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

const nav = [
  ['/', '🏠', '홈'],
  ['/projects', '📁', '프로젝트 관리'],
  ['/researchers', '👥', '연구자'],
  ['/research-notes', '📝', '연구노트'],
  ['/my-page', '🙍', '마이페이지'],
  ['/data-updates', '📌', '활동내역'],
  ['/signatures', '✍️', '서명'],
  ['/final-download', '⬇️', '최종 다운로드'],
  ['/logout', '🚪', '로그아웃']
];

export default function UserLayout({ title, children }) {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

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
      </aside>

      <section className="pn-main">
        <main className="pn-shell">
          <div className="pn-headline">
            <h1 className="pn-title">{title}</h1>
            <div style={{ alignItems: 'center', display: 'flex', gap: 8 }}>
              <p className="pn-sub" style={{ margin: 0 }}>일반 사용자 화면 · React</p>
              <Link className="pn-side-list" to="/my-page">개인 페이지</Link>
              <Link className="pn-side-list" to="/logout">로그아웃</Link>
            </div>
          </div>
          {children}
        </main>
      </section>
    </div>
  );
}
