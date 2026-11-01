import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const proxy = { '/api': {
    target: env.API_PROXY_TARGET || 'http://127.0.0.1:18080',
    rewrite: path => path.replace(/^\/api/, ''),
  } };
  return { server: { port: 18081, strictPort: true, proxy }, preview: { port: 18082, strictPort: true, proxy } };
});
