import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const djangoProxy = {
  target: 'http://127.0.0.1:8000',
  changeOrigin: true,
  secure: false
};

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/__django': {
        ...djangoProxy,
        rewrite: (path) => path.replace(/^\/__django/, '')
      },
      '/api': djangoProxy,
      '/login': djangoProxy,
      '/logout': djangoProxy,
      '/signup': djangoProxy,
      '/admin/login': djangoProxy,
      '/frontend': djangoProxy
    }
  }
});
