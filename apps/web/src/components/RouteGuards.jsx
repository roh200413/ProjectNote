import { Navigate, useLocation } from 'react-router-dom';
import { getRole, hasAuthSession } from '../utils/auth';

export function AdminRoute({ children }) {
  const location = useLocation();
  const role = getRole();
  if (role !== 'admin') {
    return <Navigate replace to={`/auth/admin-login?next=${encodeURIComponent(location.pathname)}`} />;
  }
  return children;
}

export function UserRoute({ children }) {
  const location = useLocation();
  const role = getRole();

  if (role === 'user') return children;
  if (role && role !== 'user') {
    return <Navigate replace to={`/auth/login?next=${encodeURIComponent(location.pathname)}`} />;
  }

  // role 저장이 비활성화된 브라우저에서도 서버 세션이 있으면 진입 허용
  if (hasAuthSession()) return children;

  return <Navigate replace to={`/auth/login?next=${encodeURIComponent(location.pathname)}`} />;
}
