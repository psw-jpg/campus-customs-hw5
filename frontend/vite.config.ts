import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Port 5181: 5173, 5174 and 5180 are held by older lecture apps on this machine.
// The backend (FastAPI on :8000) allows this origin via CORS.
export default defineConfig({
  plugins: [react()],
  server: { port: 5181, strictPort: true },
})
