import { fileURLToPath, URL } from 'node:url'

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiTarget = env.VITE_DEV_API_TARGET || 'http://127.0.0.1:8001'

  const proxyOptions = () => ({
    target: apiTarget,
    changeOrigin: true,
    secure: false,
    bypass(request) {
      if (request.headers.accept?.includes('text/html')) {
        return '/index.html'
      }
      return undefined
    },
  })

  return {
    plugins: [vue()],
    // The only large lazy chunk is the administrator analytics page with the
    // tree-shaken ECharts runtime. It is never loaded by student routes.
    build: {
      chunkSizeWarningLimit: 600,
    },
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      proxy: {
        '/api': proxyOptions(),
        '/resources': proxyOptions(),
        '/admin': proxyOptions(),
        '/path': proxyOptions(),
        '/profile': proxyOptions(),
        '/profile-builder': proxyOptions(),
        '/producer': proxyOptions(),
      },
    },
  }
})
