import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
export default defineConfig({
  plugins: [vue()], // 新增这一行
  server: {
    proxy: {
      '/api': {
        target: process.env.VITE_DEV_API_TARGET || 'http://127.0.0.1:5050',
        changeOrigin: true
      }
    }
  }
})
