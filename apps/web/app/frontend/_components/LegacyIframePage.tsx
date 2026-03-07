function backendOrigin() {
  return process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';
}

export default function LegacyIframePage({
  path,
  legacyPrefix = "legacy/frontend",
}: {
  path: string;
  legacyPrefix?: string;
}) {
  const prefix = legacyPrefix.replace(/^\/+|\/+$/g, "");
  const normalizedPath = path.replace(/^\/+/, "");
  const src = prefix
    ? `${backendOrigin()}/${prefix}/${normalizedPath}`
    : `${backendOrigin()}/${normalizedPath}`;

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
