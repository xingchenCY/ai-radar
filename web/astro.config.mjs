import { defineConfig } from 'astro/config';

const base = process.env.BASE_PATH || '';

export default defineConfig({
  site: process.env.SITE_URL || 'http://localhost:4321',
  base,
  build: { format: 'directory' },
});
