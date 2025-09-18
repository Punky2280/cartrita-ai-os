import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Use globalThis.process.env to avoid analyzer complaining about 'process' not defined in this context

const env = (typeof globalThis !== 'undefined' && globalThis.process && globalThis.process.env) ? globalThis.process.env : {};

// Enhanced Content Security Policy with nonce support and environment awareness
function getContentSecurityPolicy() {
  const isProduction = env.NODE_ENV === 'production';
  const apiUrl = env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const frontendUrl = env.FRONTEND_URL || 'http://localhost:3001';

  const policies = [
    "default-src 'self'",
    // Enhanced script-src: removed unsafe-inline/unsafe-eval for production
    isProduction
      ? "script-src 'self'"
      : "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    "img-src 'self' data: blob: https:",
    `connect-src 'self'
      ws://localhost:8000 http://localhost:8000 https://localhost:8000
      ws://127.0.0.1:8000 http://127.0.0.1:8000
      ws://localhost:3001 http://localhost:3001
      ws://localhost:3003 http://localhost:3003
      ${apiUrl} ${frontendUrl}
      https://fonts.googleapis.com https://fonts.gstatic.com
      https://api.openai.com https://api.deepgram.com`,
    "font-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com",
    "object-src 'none'",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'"
  ];

  if (isProduction) {
    policies.push("upgrade-insecure-requests");
  }

  // Add CSP violation reporting
  const reportUri = env.CSP_REPORT_URI || '/api/security/csp-violation';
  policies.push(`report-uri ${reportUri}`);

  return policies.join('; ').replace(/\s+/g, ' ').trim();
}

const ContentSecurityPolicy = getContentSecurityPolicy();

const nextConfig = {
  output: 'standalone',
  outputFileTracingRoot: __dirname.endsWith('/frontend') ? __dirname.slice(0, -9) : __dirname + '/../',
  images: {
    domains: ['localhost'],
    unoptimized: env.NODE_ENV === 'development',
  },
  // Note: API routes handle authentication automatically
  // No rewrites needed as we use Next.js API routes for proxying
  env: {
    NEXT_PUBLIC_API_URL: env.NEXT_PUBLIC_API_URL || 'http://localhost:3001',
    NEXT_PUBLIC_WS_URL: env.NEXT_PUBLIC_WS_URL || 'ws://localhost:3001',
    // API key should be provided in environment variables
    NEXT_PUBLIC_CARTRITA_API_KEY: env.NEXT_PUBLIC_CARTRITA_API_KEY,
  },
}

// Add CSP headers
const withSecurityHeaders = {
  ...nextConfig,
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: ContentSecurityPolicy.replace(/\n/g, ''),
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on',
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload',
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()',
          },
          {
            key: 'Cross-Origin-Embedder-Policy',
            value: 'require-corp',
          },
          {
            key: 'Cross-Origin-Opener-Policy',
            value: 'same-origin',
          },
          {
            key: 'Cross-Origin-Resource-Policy',
            value: 'same-origin',
          },
        ],
      },
    ]
  },
}

// ES Module export
export default withSecurityHeaders;
