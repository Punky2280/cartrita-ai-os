// Cartrita AI OS - Vitest Configuration
// Test configuration for comprehensive API testing

import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/__tests__/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/__tests__/**',
        '**/*.d.ts',
        '**/*.config.*',
        'dist/',
        '.next/'
      ],
      thresholds: {
        global: {
          branches: 80,
          functions: 80,
          lines: 80,
          statements: 80
        }
      }
    },
    include: [
      'src/__tests__/**/*.test.{js,ts,tsx}',
      'src/hooks/__tests__/**/*.test.{js,ts,tsx}',
      'src/components/__tests__/**/*.test.{js,ts,tsx}'
    ],
    exclude: [
      'node_modules/',
      'dist/',
      '.next/',
      '**/*.config.*'
    ]
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
})