import { Link } from 'react-router-dom';

export default function NotImplementedPage({ path, legacyEnabled }) {
  return (
    <section className="pn-page">
      <h1>React 화면 구현 진행 중</h1>
      <p className="pn-sub">
        <code>{path}</code> 경로는 아직 React 네이티브 구현이 완료되지 않았습니다.
      </p>
      <p>
        현재는 Django HTML 자동 fallback을 기본 차단했습니다. (요청사항 반영)
      </p>
      {legacyEnabled ? (
        <p className="pn-sub">현재 `VITE_ENABLE_LEGACY_PAGES=true` 이므로 레거시 fallback을 허용 중입니다.</p>
      ) : (
        <p className="pn-sub">
          테스트 시 임시로 열려면 <code>apps/web/.env.local</code>에
          <code> VITE_ENABLE_LEGACY_PAGES=true</code>를 설정 후 dev 서버를 재시작하세요.
        </p>
      )}
      <div className="pn-nav-links">
        <Link to="/auth/admin-login">관리자 로그인(React)</Link>
        <Link to="/admin/dashboard">관리자 대시보드(React)</Link>
        <Link to="/admin/users">사용자 관리(React)</Link>
        <Link to="/admin/teams">팀 관리(React)</Link>
        <Link to="/admin/tables">테이블 관리(React)</Link>
      </div>
    </section>
  );
}
