import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { '/places': {target: 'http://127.0.0.1:8000'}, '/route': {target: 'http://127.0.0.1:8000'}, '/health': {target: 'http://127.0.0.1:8000'} } },
})
