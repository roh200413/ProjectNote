export function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return '';
}

export async function apiFetch(path, options = {}) {
  const res = await fetch(path, {
    credentials: 'include',
    redirect: 'follow',
    ...options,
    headers: {
      ...(options.headers || {})
    }
  });

  if (res.redirected && (res.url.includes('/login') || res.url.includes('/admin/login'))) {
    throw new Error('로그인이 필요합니다. /auth/admin-login 에서 로그인하세요.');
  }

  const contentType = res.headers.get('content-type') || '';
  const body = contentType.includes('application/json') ? await res.json() : await res.text();

  if (!res.ok) {
    const message = typeof body === 'object' && body?.detail ? body.detail : `요청 실패 (${res.status})`;
    throw new Error(message);
  }

  if (typeof body === 'string' && body.includes('<!doctype html')) {
    throw new Error('API 응답 대신 HTML이 반환되었습니다. 로그인 상태를 확인하세요.');
  }

  return body;
}

export function formEncoded(payload) {
  const params = new URLSearchParams();
  Object.entries(payload).forEach(([key, value]) => {
    if (value !== undefined && value !== null) params.append(key, String(value));
  });
  return params;
}
