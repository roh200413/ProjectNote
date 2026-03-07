import { NextRequest, NextResponse } from 'next/server';

import { backendBaseUrl, copySetCookies, forwardCookies } from '@/lib/backend';

export async function GET(req: NextRequest, { params }: { params: { projectId: string } }) {
  const search = req.nextUrl.search || '';
  const response = await fetch(`${backendBaseUrl()}/api/v1/projects/${params.projectId}/research-notes/export-pdf${search}`, {
    method: 'GET',
    headers: { cookie: forwardCookies(req) },
    cache: 'no-store',
  });

  const arrayBuffer = await response.arrayBuffer();
  const proxied = new NextResponse(arrayBuffer, {
    status: response.status,
    headers: {
      'content-type': response.headers.get('content-type') || 'application/pdf',
      'content-disposition': response.headers.get('content-disposition') || '',
      'x-merged-file-count': response.headers.get('x-merged-file-count') || '0',
      'x-total-file-count': response.headers.get('x-total-file-count') || '0',
    },
  });
  copySetCookies(response, proxied);
  return proxied;
}
