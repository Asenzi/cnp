import { defineConfig } from '@vben/vite-config';

import ElementPlus from 'unplugin-element-plus/vite';

export default defineConfig(async () => {
  return {
    application: {},
    vite: {
      optimizeDeps: {
        // Keep dependency optimization enabled so Vite can wrap CommonJS
        // packages correctly in dev. Element Plus is excluded because the
        // style side-effect imports currently trigger a Rolldown unicode-path
        // panic on Windows when the workspace path contains non-ASCII chars.
        exclude: ['element-plus'],
      },
      resolve: {
        alias: [
          { find: /^dayjs$/, replacement: 'dayjs/esm/index.js' },
          {
            find: /^dayjs\/plugin\/(.+)\.js$/,
            replacement: 'dayjs/esm/plugin/$1/index.js',
          },
          {
            find: /^dayjs\/locale\/(.+)$/,
            replacement: 'dayjs/esm/locale/$1.js',
          },
        ],
      },
      plugins: [
        ElementPlus({
          format: 'esm',
        }),
      ],
      server: {
        proxy: {
          '/api': {
            changeOrigin: true,
            target: 'http://127.0.0.1:8001',
            ws: true,
          },
        },
      },
    },
  };
});
