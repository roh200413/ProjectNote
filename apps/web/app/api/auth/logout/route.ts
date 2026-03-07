import { NextRequest, NextResponse } from 'next/server';

import { backendBaseUrl, copySetCookies, forwardCookies } from '@/lib/backend';

export async function POST(req: NextRequest) {
  const response = await fetch(`${backendBaseUrl()}/api/v1/auth/logout`, {
    method: 'POST',
    headers: {
      cookie: forwardCookies(req),
    },
  });

  const bodyText = await response.text();
  const proxied = new NextResponse(bodyText, {
    status: response.status,
    headers: { 'content-type': response.headers.get('content-type') || 'application/json' },
  });
  copySetCookies(response, proxied);
  return proxied;
}
