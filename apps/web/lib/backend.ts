import { NextRequest, NextResponse } from 'next/server';

const DEFAULT_API_BASE_URL = 'http://127.0.0.1:8000';

export function backendBaseUrl() {
  return process.env.NEXT_PUBLIC_API_BASE_URL || DEFAULT_API_BASE_URL;
}

export function forwardCookies(req: NextRequest): string {
  return req.headers.get('cookie') || '';
}

export function copySetCookies(from: Response, to: NextResponse) {
  const anyHeaders = from.headers as Headers & { getSetCookie?: () => string[] };
  const setCookies = typeof anyHeaders.getSetCookie === 'function' ? anyHeaders.getSetCookie() : [];
  if (setCookies.length > 0) {
    for (const value of setCookies) {
      to.headers.append('set-cookie', value);
    }
    return;
  }

  const fallback = from.headers.get('set-cookie');
  if (fallback) {
    to.headers.set('set-cookie', fallback);
  }
}
