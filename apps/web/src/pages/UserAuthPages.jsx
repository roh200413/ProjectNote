import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { apiFetch, formEncoded, getCookie } from '../utils/http';
import { setRole } from '../utils/auth';

export function LoginPage() {
  const nav = useNavigate();
  const [searchParams] = useSearchParams();
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin1234');
  const [error, setError] = useState('');

  async function submit(e) {
    e.preventDefault();
    setError('');
    try {
      await fetch('/login', { credentials: 'include' });
      const nextUrl = searchParams.get('next') || '/';
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
      setRole('user');
      nav(nextUrl, { replace: true });
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <main className="pn-auth-wrap">
      <form className="pn-auth-card" onSubmit={submit}>
        <h1>일반 사용자 로그인 (React)</h1>
        <p className="pn-sub">관리자 로그인은 별도 경로를 사용하세요.</p>
        <Link className="pn-side-list" to="/auth/admin-login">관리자 로그인으로 이동</Link>
        <Link className="pn-side-list" to="/auth/signup">회원가입 하러가기</Link>
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
  const nav = useNavigate();
  const [form, setForm] = useState({
    username: '',
    display_name: '',
    email: '',
    password: '',
    role: 'member',
    team_name: '',
    team_description: '',
    team_code: ''
  });
  const [msg, setMsg] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetch('/signup', { credentials: 'include' }).catch(() => {});
  }, []);

  const isOwner = useMemo(() => form.role === 'owner', [form.role]);

  function validate() {
    if (!form.username || !form.display_name || !form.email || !form.password) {
      return '아이디/이름/이메일/비밀번호는 필수입니다.';
    }
    if (isOwner && !form.team_name.trim()) {
      return '소유자 가입 시 팀 이름은 필수입니다.';
    }
    if (!isOwner && form.team_name.trim() && !form.team_code.trim()) {
      return '팀 이름을 입력했다면 팀 코드도 함께 입력하세요.';
    }
    return '';
  }

  async function submit(e) {
    e.preventDefault();
    setError('');
    setMsg('');

    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        username: form.username.trim(),
        display_name: form.display_name.trim(),
        email: form.email.trim(),
        password: form.password,
        role: form.role,
        team_name: form.team_name.trim(),
        team_description: isOwner ? form.team_description.trim() : '',
        team_code: isOwner ? '' : form.team_code.trim()
      };

      const created = await apiFetch('/api/v1/auth/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': getCookie('csrftoken')
        },
        body: formEncoded(payload)
      });

      setMsg(`가입 완료: ${created.username} (승인 후 로그인 가능합니다)`);
      setForm({ username: '', display_name: '', email: '', password: '', role: 'member', team_name: '', team_description: '', team_code: '' });
      setTimeout(() => nav('/auth/login'), 1200);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="pn-auth-wrap">
      <form className="pn-auth-card" onSubmit={submit}>
        <h1>회원가입 (React)</h1>
        <p className="pn-sub">역할에 맞게 팀 정보를 입력하세요.</p>
        {error && <p className="pn-err">{error}</p>}
        {msg && <p className="pn-sub">{msg}</p>}

        <label>아이디</label>
        <input placeholder="아이디" required value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} />
        <label>이름</label>
        <input placeholder="이름" required value={form.display_name} onChange={(e) => setForm({ ...form, display_name: e.target.value })} />
        <label>이메일</label>
        <input placeholder="이메일" required type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <label>비밀번호</label>
        <input placeholder="비밀번호" required type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />

        <label>가입 유형</label>
        <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value, team_description: '', team_code: '' })}>
          <option value="member">일반</option>
          <option value="owner">소유자</option>
        </select>

        <label>팀 이름</label>
        <input placeholder={isOwner ? '새로 만들 팀 이름' : '기존 팀 이름(선택)'} value={form.team_name} onChange={(e) => setForm({ ...form, team_name: e.target.value })} />

        {isOwner ? (
          <>
            <label>팀 설명</label>
            <input placeholder="팀 설명(선택)" value={form.team_description} onChange={(e) => setForm({ ...form, team_description: e.target.value })} />
          </>
        ) : (
          <>
            <label>팀 코드</label>
            <input placeholder="기존 팀 코드(팀 이름 입력 시 필수)" value={form.team_code} onChange={(e) => setForm({ ...form, team_code: e.target.value })} />
          </>
        )}

        <button disabled={submitting} type="submit">{submitting ? '가입 중...' : '가입'}</button>
        <Link className="pn-side-list" to="/auth/login">로그인으로 돌아가기</Link>
      </form>
    </main>
  );
}
