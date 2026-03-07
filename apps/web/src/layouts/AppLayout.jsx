import { Link } from 'react-router-dom';

const quickLinks = [
  ['/', '홈'],
  ['/projects', '프로젝트'],
  ['/research-notes', '연구노트'],
  ['/researchers', '연구자'],
  ['/my-page', '마이페이지'],
  ['/admin/dashboard', '관리자']
];

export default function AppLayout({ children }) {
  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>ProjectNote React Workspace</h1>
        <nav>
          {quickLinks.map(([to, label]) => (
            <Link key={to} to={to}>
              {label}
            </Link>
          ))}
        </nav>
      </header>
      <main>{children}</main>
    </div>
  );
}
