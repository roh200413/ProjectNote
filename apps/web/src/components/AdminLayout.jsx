import { Link } from 'react-router-dom';

const navItems = [
  { key: 'dashboard', title: '대시보드', to: '/admin/dashboard' },
  { key: 'users', title: '사용자 관리', to: '/admin/users' },
  { key: 'teams', title: '팀 관리', to: '/admin/teams' },
  { key: 'tables', title: '테이블 관리', to: '/admin/tables' }
];

export default function AdminLayout({ active, title, children }) {
  return (
    <section className="pn-page">
      <div className="pn-headline">
        <h1>{title}</h1>
        <p className="pn-sub">ADMIN 콘솔 · React</p>
      </div>
      <div className="pn-admin-grid">
        <aside className="pn-card">
          <h3 style={{ marginTop: 0 }}>메뉴</h3>
          <div className="pn-side-menu">
            {navItems.map((item) => (
              <Link className={`pn-side-list ${active === item.key ? 'active' : ''}`} key={item.key} to={item.to}>
                {item.title}
              </Link>
            ))}
          </div>
        </aside>
        <div>{children}</div>
      </div>
    </section>
  );
}
