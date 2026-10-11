import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      // Deep imports into Monaco's ESM build (the package "exports" map does
      // not expose its CSS files). Used only by the lean Monaco entry module.
      'monaco-esm': fileURLToPath(new URL('./node_modules/monaco-editor/esm/vs', import.meta.url)),
    },
  },
  build: {
    // Monaco's core is ~3.9 MB (~1 MB gzip). It is its own chunk, loaded only
    // when the coding workspace opens; the main app bundle stays ~330 kB.
    chunkSizeWarningLimit: 4500,
  },
  server: {
    port: 5173,
  },
})
