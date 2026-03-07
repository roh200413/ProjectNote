import { NextRequest, NextResponse } from 'next/server';

import { backendBaseUrl, copySetCookies, forwardCookies } from '@/lib/backend';

export async function POST(req: NextRequest) {
  const payload = await req.json();
  const form = new URLSearchParams();
  form.set('username', String(payload.username || ''));
  form.set('password', String(payload.password || ''));

  const response = await fetch(`${backendBaseUrl()}/api/v1/auth/login`, {
    method: 'POST',
    headers: {
      'content-type': 'application/x-www-form-urlencoded',
      cookie: forwardCookies(req),
    },
    body: form.toString(),
  });

  const bodyText = await response.text();
  const proxied = new NextResponse(bodyText, {
    status: response.status,
    headers: { 'content-type': response.headers.get('content-type') || 'application/json' },
  });
  copySetCookies(response, proxied);
  return proxied;
}
