import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/health': 'http://localhost:8000',
      '/auth': 'http://localhost:8000',
      '/budget': 'http://localhost:8000',
    }
  },
  build: {
    outDir: 'dist'
  }
})
