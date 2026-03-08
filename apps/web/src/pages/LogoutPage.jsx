import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { clearRole } from '../utils/auth';

export default function LogoutPage() {
  const nav = useNavigate();

  useEffect(() => {
    fetch('/logout', { credentials: 'include' })
      .finally(() => {
        clearRole();
        nav('/auth/login', { replace: true });
      });
  }, [nav]);

  return <main className="pn-auth-wrap"><div className="pn-auth-card">로그아웃 중...</div></main>;
}
