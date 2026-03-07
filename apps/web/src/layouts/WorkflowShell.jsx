import { Link } from 'react-router-dom';

const links = [
  ['/','홈'],
  ['/projects','프로젝트 관리'],
  ['/researchers','연구자'],
  ['/research-notes','연구노트'],
  ['/my-page','마이페이지'],
  ['/signatures','서명'],
  ['/final-download','최종 다운로드']
];

export default function WorkflowShell({ pageTitle, actionsHtml, contentHtml }) {
  return (
    <div className="pn-layout">
      <aside className="pn-sidebar">
        <div className="pn-side-head">
          <div className="pn-logo">Project Note</div>
        </div>
        <nav className="pn-menu">
          {links.map(([to, label]) => (
            <Link key={to} className="pn-side-link" to={to}>{label}</Link>
          ))}
        </nav>
      </aside>
      <section className="pn-main">
        <main className="pn-shell">
          <div className="pn-head">
            <div>
              <h1 className="pn-title">{pageTitle || 'ProjectNote'}</h1>
              <div className="pn-sub">기존 HTML 템플릿 UI를 React에서 동일 구조로 렌더링</div>
            </div>
            <div dangerouslySetInnerHTML={{ __html: actionsHtml }} />
          </div>
          <div dangerouslySetInnerHTML={{ __html: contentHtml }} />
        </main>
      </section>
    </div>
  );
}
