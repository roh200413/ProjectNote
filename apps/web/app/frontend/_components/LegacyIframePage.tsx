function backendOrigin() {
  return process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';
}

export default function LegacyIframePage({ path }: { path: string }) {
  const src = `${backendOrigin()}/legacy/frontend/${path}`;

  return (
    <main style={{ minHeight: '100vh', padding: 0, display: 'block' }}>
      <iframe
        src={src}
        title={`legacy-${path}`}
        style={{ width: '100%', height: '100vh', border: '0', display: 'block' }}
      />
    </main>
  );
}
