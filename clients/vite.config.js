import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'
import vue from '@vitejs/plugin-vue'
 
// https://vitejs.dev/config/
export default defineConfig({
  server: {
    watch: {
      usePolling: true,   // force Vite à surveiller les fichiers par polling (utile sur WSL/Windows)
      interval: 100
    }
  },
  plugins: [
    tailwindcss,
    vue(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  }
})

