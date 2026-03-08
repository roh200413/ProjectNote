import { Navigate, useLocation } from 'react-router-dom';
import { getRole } from '../utils/auth';

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
  if (role !== 'user') {
    return <Navigate replace to={`/auth/login?next=${encodeURIComponent(location.pathname)}`} />;
  }
  return children;
}
