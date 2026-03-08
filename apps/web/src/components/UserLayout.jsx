import { Link } from 'react-router-dom';

const nav = [
  ['/', '홈'],
  ['/projects', '프로젝트'],
  ['/researchers', '연구자'],
  ['/research-notes', '연구노트'],
  ['/my-page', '마이페이지'],
  ['/data-updates', '활동내역'],
  ['/signatures', '서명'],
  ['/final-download', '최종 다운로드'],
  ['/auth/login', '로그인']
];

export default function UserLayout({ title, children }) {
  return (
    <section className="pn-page">
      <div className="pn-headline">
        <h1>{title}</h1>
        <p className="pn-sub">일반 사용자 화면 · React</p>
      </div>
      <div className="pn-card" style={{ marginBottom: 12 }}>
        <div className="pn-nav-links" style={{ flexWrap: 'wrap' }}>
          {nav.map(([to, label]) => (
            <Link key={to} to={to}>{label}</Link>
          ))}
        </div>
      </div>
      {children}
    </section>
  );
}
