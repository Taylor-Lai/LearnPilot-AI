import { fileURLToPath, URL } from 'node:url'

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiTarget = env.VITE_DEV_API_TARGET || 'http://127.0.0.1:8001'

  const proxyOptions = {
    target: apiTarget,
    changeOrigin: true,
    secure: false,
  }

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      proxy: {
        '/api': proxyOptions,
        '/resources': proxyOptions,
        '/admin': proxyOptions,
        '/path': proxyOptions,
        '/profile': proxyOptions,
        '/profile-builder': proxyOptions,
        '/producer': proxyOptions,
      },
    },
  }
})
