// @ts-check
import { defineConfig } from 'astro/config';

import tailwindcss from '@tailwindcss/vite';

// https://astro.build/config
export default defineConfig({
  site: 'https://kopani.netlify.app/',   // ← add this
  vite: {
    plugins: [tailwindcss()],
    optimizeDeps: { exclude: ['better-sqlite3'] },
    ssr: { external: ['better-sqlite3'] },
  }
});