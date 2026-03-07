import { useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';

function resolveBackendPath(backendPath, params) {
  return typeof backendPath === 'function' ? backendPath(params) : backendPath;
}

export default function LegacyTemplatePage({ backendPath }) {
  const params = useParams();
  const [loaded, setLoaded] = useState(false);
  const src = useMemo(() => `/__django${resolveBackendPath(backendPath, params)}`, [backendPath, params]);

  return (
    <div className="legacy-frame-wrap">
      {!loaded && (
        <div className="legacy-loading">
          Django 페이지를 불러오는 중입니다... (백엔드: http://localhost:8000)
        </div>
      )}
      <iframe
        onLoad={() => setLoaded(true)}
        src={src}
        style={{ border: 'none', display: 'block', minHeight: '100vh', width: '100%' }}
        title={src}
      />
    </div>
  );
}
