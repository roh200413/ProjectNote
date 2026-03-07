import { NextRequest, NextResponse } from 'next/server';

import { backendBaseUrl, copySetCookies, forwardCookies } from '@/lib/backend';

export async function POST(req: NextRequest, { params }: { params: { projectId: string } }) {
  const formData = await req.formData();

  const response = await fetch(`${backendBaseUrl()}/api/v1/projects/${params.projectId}/research-notes/upload`, {
    method: 'POST',
    headers: { cookie: forwardCookies(req) },
    body: formData,
  });

  const bodyText = await response.text();
  const proxied = new NextResponse(bodyText, {
    status: response.status,
    headers: { 'content-type': response.headers.get('content-type') || 'application/json' },
  });
  copySetCookies(response, proxied);
  return proxied;
}
