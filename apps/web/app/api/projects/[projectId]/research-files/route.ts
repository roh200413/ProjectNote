import { NextRequest, NextResponse } from 'next/server';

import { backendBaseUrl, copySetCookies, forwardCookies } from '@/lib/backend';

export async function GET(req: NextRequest, { params }: { params: { projectId: string } }) {
  const response = await fetch(`${backendBaseUrl()}/api/v1/projects/${params.projectId}/research-files`, {
    method: 'GET',
    headers: { cookie: forwardCookies(req) },
    cache: 'no-store',
  });

  const bodyText = await response.text();
  const proxied = new NextResponse(bodyText, {
    status: response.status,
    headers: { 'content-type': response.headers.get('content-type') || 'application/json' },
  });
  copySetCookies(response, proxied);
  return proxied;
}
