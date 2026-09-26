import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// En développement, les appels /api partent vers l'api Python locale (uvicorn, port 8000).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
