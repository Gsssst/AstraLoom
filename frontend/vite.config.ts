import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const vendorChunk = (id: string) => {
  if (!id.includes('node_modules')) return undefined
  if (id.includes('/react/') || id.includes('/react-dom/') || id.includes('/react-router-dom/') || id.includes('/scheduler/')) {
    return 'vendor-react'
  }
  if (id.includes('/antd/') || id.includes('/@ant-design/') || id.includes('/rc-') || id.includes('/@rc-component/')) {
    return 'vendor-antd'
  }
  if (id.includes('/react-markdown/') || id.includes('/remark-gfm/') || id.includes('/rehype-katex/') || id.includes('/katex/')) {
    return 'vendor-markdown'
  }
  if (id.includes('/react-pdf/') || id.includes('/pdfjs-dist/')) {
    return 'vendor-pdf'
  }
  if (id.includes('/axios/') || id.includes('/zustand/')) {
    return 'vendor-state'
  }
  return 'vendor-misc'
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: vendorChunk,
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/docs': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
