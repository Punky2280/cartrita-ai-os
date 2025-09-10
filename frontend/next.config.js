/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  outputFileTracingRoot: require('path').join(__dirname, '../../'),
  images: {
    domains: ['localhost'],
    unoptimized: process.env.NODE_ENV === 'development',
  },
  // Note: API routes handle authentication automatically
  // No rewrites needed as we use Next.js API routes for proxying
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000',
    NEXT_PUBLIC_CARTRITA_API_KEY: process.env.NEXT_PUBLIC_CARTRITA_API_KEY || 'dev-api-key-2025',
  },
  // Turbopack configuration (Next.js 15.3+)
  turbopack: {
    resolveAlias: {
      // Optimize common imports
      'react': 'react',
      'react-dom': 'react-dom',
    },
    resolveExtensions: ['.mdx', '.tsx', '.ts', '.jsx', '.js', '.mjs', '.json'],
  },
}

module.exports = nextConfig