export function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return '';
}

function normalizeErrorDetail(detail, status) {
  if (typeof detail === 'string' && detail.trim()) return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0];
    if (typeof first === 'string') return first;
    if (first && typeof first === 'object' && first.msg) return String(first.msg);
  }
  if (detail && typeof detail === 'object' && detail.msg) return String(detail.msg);
  return `요청 실패 (${status})`;
}

export async function apiFetch(path, options = {}) {
  let res;
  try {
    res = await fetch(path, {
      credentials: 'include',
      redirect: 'follow',
      ...options,
      headers: {
        ...(options.headers || {})
      }
    });
  } catch (error) {
    throw new Error('백엔드 서버에 연결할 수 없습니다. Django 서버 실행 상태와 Vite 프록시 설정을 확인하세요.');
  }

  if (res.redirected && (res.url.includes('/login') || res.url.includes('/admin/login'))) {
    throw new Error('로그인이 필요합니다. /auth/admin-login 에서 로그인하세요.');
  }

  const contentType = res.headers.get('content-type') || '';
  const body = contentType.includes('application/json') ? await res.json() : await res.text();

  if (!res.ok) {
    const detail = typeof body === 'object' && body ? body.detail : '';
    throw new Error(normalizeErrorDetail(detail, res.status));
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
