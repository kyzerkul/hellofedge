import { fileURLToPath } from 'node:url'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [react()],
  // Les gardes du design system lisent docs/design.md, hors du dossier du cockpit.
  server: {
    fs: {
      allow: [fileURLToPath(new URL('.', import.meta.url)), fileURLToPath(new URL('../docs', import.meta.url))],
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    // Les gardes lisent les feuilles de style en texte brut (`?raw`) ; les autres restent ignorées.
    css: { include: [/\.css\?raw$/] },
  },
})
