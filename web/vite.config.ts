import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/流水线': 'http://localhost:8000',
      '/智能体': 'http://localhost:8000',
      '/审批': 'http://localhost:8000',
      '/配置': 'http://localhost:8000',
      '/健康': 'http://localhost:8000',
    }
  }
})
