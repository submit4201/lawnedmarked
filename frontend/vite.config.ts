import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    proxy: {
      '/api': 'http://localhost:8008',
      '/state': 'http://localhost:8008',
      '/history': 'http://localhost:8008',
      '/health': 'http://localhost:8008',
    }
  }
})
