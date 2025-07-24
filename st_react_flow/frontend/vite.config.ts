import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Streamlit injects a global `parent.postMessage`
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "../build",
    emptyOutDir: true
  },
  server: {
    port: 5173,
    strictPort: true
  }
})
