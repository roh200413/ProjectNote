export default function AdminShell({ pageTitle, actionsHtml, contentHtml }) {
  return (
    <section className="pn-main">
      <main className="pn-shell">
        <div className="pn-head">
          <div>
            <h1 className="pn-title">{pageTitle || 'ProjectNote Admin'}</h1>
            <div className="pn-sub">관리자 전용 콘솔 화면</div>
          </div>
          <div dangerouslySetInnerHTML={{ __html: actionsHtml }} />
        </div>
        <div dangerouslySetInnerHTML={{ __html: contentHtml }} />
      </main>
    </section>
  );
}
