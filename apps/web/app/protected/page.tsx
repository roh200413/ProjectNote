import Link from 'next/link';
import { headers } from 'next/headers';

import type { GetApiV1AuthMeResponse as MeResponse } from '../../../../packages/types/generated/api-types';

async function readSession() {
  const cookie = headers().get('cookie') || '';
  const host = headers().get('host') || '127.0.0.1:3000';
  const response = await fetch(`http://${host}/api/auth/me`, {
    cache: 'no-store',
    headers: {
      cookie,
    },
  });
  return response;
}

export default async function ProtectedPage() {
  const response = await readSession();
  let payload: MeResponse = {};
  try {
    payload = (await response.json()) as MeResponse;
  } catch {
    payload = { detail: 'invalid response' };
  }

  if (!response.ok) {
    return (
      <main>
        <section className="card">
          <span className="badge">protected</span>
          <h1>권한 없는 접근 차단</h1>
          <p className="err">{payload.detail || '인증이 필요합니다.'}</p>
          <Link href="/">홈으로</Link>
        </section>
      </main>
    );
  }

  return (
    <main>
      <section className="card">
        <span className="badge">protected</span>
        <h1>권한 페이지 접근 성공</h1>
        <p className="ok">세션이 유효합니다.</p>
        <pre>{JSON.stringify(payload.user ?? {}, null, 2)}</pre>
        <Link href="/">홈으로</Link>
      </section>
    </main>
  );
}
