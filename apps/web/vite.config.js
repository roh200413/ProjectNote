import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const legacyEnabled = env.VITE_ENABLE_LEGACY_PAGES === 'true';

  const djangoProxy = {
    target: 'http://127.0.0.1:8000',
    changeOrigin: true,
    secure: false
  };

  const proxy = {
    '/api': djangoProxy,
    '/login': djangoProxy,
    '/logout': djangoProxy,
    '/signup': djangoProxy,
    '/admin/login': djangoProxy
  };

  if (legacyEnabled) {
    proxy['/__django'] = {
      ...djangoProxy,
      rewrite: (path) => path.replace(/^\/__django/, '')
    };
    proxy['/frontend'] = djangoProxy;
  }

  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy
    }
  };
});
