'use client';

import Link from 'next/link';
import { useCallback, useEffect, useMemo, useState } from 'react';

import type { GetApiV1AuthMeResponse as MePayload, GetApiV1HealthResponse as HealthPayload } from '../../../packages/types/generated/api-types';

const DEFAULT_API_BASE_URL = '/api';

export default function HomePage() {
  const apiBaseUrl = useMemo(() => process.env.NEXT_PUBLIC_API_BASE_URL || DEFAULT_API_BASE_URL, []);
  const [health, setHealth] = useState<HealthPayload | null>(null);
  const [healthError, setHealthError] = useState<string>('');
  const [me, setMe] = useState<MePayload | null>(null);
  const [bridgeMessage, setBridgeMessage] = useState<string>('');
  const [username, setUsername] = useState('member-login');
  const [password, setPassword] = useState('admin1234');

  const checkMe = useCallback(async () => {
    const response = await fetch('/api/auth/me', { cache: 'no-store' });
    const payload = (await response.json()) as MePayload;
    setMe(payload);
    if (!response.ok) {
      throw new Error(payload.detail || `me-check failed: ${response.status}`);
    }
    return payload;
  }, []);

  useEffect(() => {
    const run = async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/health`, { cache: 'no-store' });
        if (!response.ok) {
          throw new Error(`Health request failed: ${response.status}`);
        }
        const payload = (await response.json()) as HealthPayload;
        setHealth(payload);
      } catch (err) {
        setHealthError(err instanceof Error ? err.message : 'Unknown error');
      }

      try {
        await checkMe();
      } catch {
        // ignore initial unauthenticated state
      }
    };
    run();
  }, [apiBaseUrl, checkMe]);

  const onLogin = async () => {
    setBridgeMessage('로그인 처리 중...');
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    const payload = (await response.json()) as Record<string, unknown>;
    if (!response.ok) {
      setBridgeMessage(String(payload.detail || `로그인 실패 (${response.status})`));
      return;
    }
    setBridgeMessage('로그인 성공');
    await checkMe();
  };

  const onLogout = async () => {
    setBridgeMessage('로그아웃 처리 중...');
    const response = await fetch('/api/auth/logout', { method: 'POST' });
    const payload = (await response.json()) as Record<string, unknown>;
    if (!response.ok) {
      setBridgeMessage(String(payload.detail || `로그아웃 실패 (${response.status})`));
      return;
    }
    setBridgeMessage('로그아웃 완료');
    await checkMe().catch(() => undefined);
  };

  return (
    <main>
      <section className="card">
        <span className="badge">apps/web · Next.js auth bridge bootstrap</span>
        <h1 style={{ margin: '12px 0 6px' }}>ProjectNote Web Health + Session Bridge</h1>
        <p className="muted" style={{ marginTop: 0 }}>
          NEXT_PUBLIC_API_BASE_URL: <strong>{apiBaseUrl}</strong>
        </p>

        {health && <p className="ok" style={{ fontWeight: 600 }}>Backend health: {health.status}</p>}
        {healthError && <p className="err" style={{ fontWeight: 600 }}>Backend health error: {healthError}</p>}

        <hr style={{ border: 0, borderTop: '1px solid #e2e8f0', margin: '16px 0' }} />
        <h3 style={{ marginBottom: 8 }}>Django 세션 인증 브릿지</h3>
        <div style={{ display: 'grid', gap: 8, marginBottom: 10 }}>
          <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="username" style={{ padding: 10 }} />
          <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" placeholder="password" style={{ padding: 10 }} />
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button onClick={onLogin} style={{ padding: '8px 12px' }}>로그인</button>
            <button onClick={() => checkMe().then(() => setBridgeMessage('me-check 성공')).catch((e) => setBridgeMessage(e.message))} style={{ padding: '8px 12px' }}>me-check</button>
            <button onClick={onLogout} style={{ padding: '8px 12px' }}>로그아웃</button>
            <Link href="/protected" style={{ padding: '8px 12px', border: '1px solid #cbd5e1', borderRadius: 6 }}>권한페이지 이동</Link>
            <Link href="/frontend/projects" style={{ padding: '8px 12px', border: '1px solid #cbd5e1', borderRadius: 6 }}>프로젝트(이관)</Link>
            <Link href="/frontend/research-notes" style={{ padding: '8px 12px', border: '1px solid #cbd5e1', borderRadius: 6 }}>연구노트(이관)</Link>
          </div>
        </div>
        {bridgeMessage && <p style={{ margin: '0 0 8px' }}>{bridgeMessage}</p>}

        <h3 style={{ marginBottom: 8 }}>me-check payload</h3>
        <pre>{JSON.stringify(me ?? { detail: 'not checked' }, null, 2)}</pre>
      </section>
    </main>
  );
}
