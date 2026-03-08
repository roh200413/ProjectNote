import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiFetch, formEncoded, getCookie } from '../utils/http';

export function LoginPage() {
  const nav = useNavigate();
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin1234');
  const [error, setError] = useState('');

  async function submit(e) {
    e.preventDefault();
    setError('');
    try {
      await fetch('/login', { credentials: 'include' });
      const res = await fetch('/login', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': getCookie('csrftoken')
        },
        body: formEncoded({ username, password, next: '/frontend/workflows' })
      });
      if (!res.ok) throw new Error(`로그인 실패 (${res.status})`);
      nav('/');
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <main className="pn-auth-wrap">
      <form className="pn-auth-card" onSubmit={submit}>
        <h1>로그인 (React)</h1>
        {error && <p className="pn-err">{error}</p>}
        <label>아이디</label>
        <input value={username} onChange={(e) => setUsername(e.target.value)} />
        <label>비밀번호</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        <button type="submit">로그인</button>
      </form>
    </main>
  );
}

export function SignupPage() {
  const [form, setForm] = useState({ username: '', display_name: '', email: '', password: '', role: 'member', team_name: '', team_description: '', team_code: '' });
  const [msg, setMsg] = useState('');
  const [error, setError] = useState('');

  async function submit(e) {
    e.preventDefault();
    setError('');
    setMsg('');
    try {
      const created = await apiFetch('/api/v1/auth/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': getCookie('csrftoken')
        },
        body: formEncoded(form)
      });
      setMsg(`가입 완료: ${created.username}`);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <main className="pn-auth-wrap">
      <form className="pn-auth-card" onSubmit={submit}>
        <h1>회원가입 (React)</h1>
        {error && <p className="pn-err">{error}</p>}
        {msg && <p className="pn-sub">{msg}</p>}
        <input placeholder="아이디" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} />
        <input placeholder="이름" value={form.display_name} onChange={(e) => setForm({ ...form, display_name: e.target.value })} />
        <input placeholder="이메일" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <input placeholder="비밀번호" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
        <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
          <option value="member">일반</option>
          <option value="owner">소유자</option>
        </select>
        <input placeholder="팀 이름" value={form.team_name} onChange={(e) => setForm({ ...form, team_name: e.target.value })} />
        <input placeholder="팀 설명" value={form.team_description} onChange={(e) => setForm({ ...form, team_description: e.target.value })} />
        <input placeholder="팀 코드" value={form.team_code} onChange={(e) => setForm({ ...form, team_code: e.target.value })} />
        <button type="submit">가입</button>
      </form>
    </main>
  );
}
