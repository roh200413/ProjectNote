import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { formEncoded, getCookie } from '../utils/http';
import { setRole } from '../utils/auth';

export default function AdminLoginPage() {
  const nav = useNavigate();
  const [searchParams] = useSearchParams();
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin1234');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await fetch('/admin/login', { credentials: 'include' });
      const csrf = getCookie('csrftoken');
      const nextUrl = searchParams.get('next') || '/admin/dashboard';
      const res = await fetch('/admin/login', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': csrf
        },
        body: formEncoded({ username, password, next: '/frontend/admin/dashboard' })
      });

      if (!res.ok) throw new Error(`로그인 실패 (${res.status})`);
      setRole('admin');
      nav(nextUrl, { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="pn-auth-wrap">
      <form className="pn-auth-card" onSubmit={handleSubmit}>
        <h1>관리자 로그인 (React)</h1>
        <p className="pn-sub">관리자 화면은 별도 로그인으로 진입합니다.</p>
        {error && <p className="pn-err">{error}</p>}
        <label>아이디</label>
        <input onChange={(e) => setUsername(e.target.value)} value={username} />
        <label>비밀번호</label>
        <input onChange={(e) => setPassword(e.target.value)} type="password" value={password} />
        <button disabled={loading} type="submit">{loading ? '로그인 중...' : '로그인'}</button>
      </form>
    </main>
  );
}
