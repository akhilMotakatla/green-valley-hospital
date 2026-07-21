import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const dirname = path.dirname(fileURLToPath(import.meta.url));

// Tests live under tests/frontend at the project root (per QA convention),
// not under src/frontend, so they're included via an absolute-ish relative
// glob and resolved against this project's src/ via the @ alias.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(dirname, './src'),
    },
  },
  server: {
    fs: {
      allow: [path.resolve(dirname, '../..')],
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: [path.resolve(dirname, './vitest.setup.ts')],
    include: ['../../tests/frontend/**/*.test.{ts,tsx}'],
  },
});
