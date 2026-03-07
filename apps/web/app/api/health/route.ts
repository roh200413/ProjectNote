import { NextResponse } from 'next/server';

import { backendBaseUrl } from '@/lib/backend';

export async function GET() {
  const response = await fetch(`${backendBaseUrl()}/api/v1/health`, { cache: 'no-store' });
  const bodyText = await response.text();
  return new NextResponse(bodyText, {
    status: response.status,
    headers: { 'content-type': response.headers.get('content-type') || 'application/json' },
  });
}
