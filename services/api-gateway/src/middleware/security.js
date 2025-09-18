/* eslint-env node */
const Joi = require('joi');

// Enhanced CSP policy generator
function getEnhancedCSP() {
  const frontendUrl = process.env.FRONTEND_URL || 'http://localhost:3001';
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const isProduction = process.env.NODE_ENV === 'production';

  const policies = [
    'default-src \'self\'',
    'script-src \'self\'' + (isProduction ? '' : ` ${frontendUrl}`), // Removed unsafe-inline/unsafe-eval
    'style-src \'self\' \'unsafe-inline\' https://fonts.googleapis.com',
    'img-src \'self\' data: blob: https:',
    `connect-src 'self' ${apiUrl} ${frontendUrl} ws: wss: https://fonts.googleapis.com https://fonts.gstatic.com`,
    'font-src \'self\' https://fonts.googleapis.com https://fonts.gstatic.com',
    'object-src \'none\'',
    'frame-ancestors \'none\'',
    'base-uri \'self\'',
    'form-action \'self\''
  ];

  if (isProduction) {
    policies.push('upgrade-insecure-requests');
  }

  // Add CSP violation reporting
  const reportUri = process.env.CSP_REPORT_URI || '/api/security/csp-violation';
  policies.push(`report-uri ${reportUri}`);

  return policies.join('; ');
}

// Input validation schemas
const inputSchemas = {
  chatRequest: {
    type: 'object',
    required: ['message'],
    properties: {
      message: {
        type: 'string',
        minLength: 1,
        maxLength: 10000,
        pattern: '^[^<>]*$' // Basic XSS prevention
      },
      context: { type: 'object' },
      agentOverride: {
        type: 'string',
        enum: ['research', 'code', 'computer_use', 'knowledge', 'task']
      },
      stream: { type: 'boolean' }
    }
  },
  headers: {
    type: 'object',
    properties: {
      'x-api-key': { type: 'string', minLength: 32 }
    }
  }
};

// Security headers configuration with enhanced CSP
const securityHeaders = {
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'X-XSS-Protection': '1; mode=block',
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
  'Content-Security-Policy': getEnhancedCSP(),
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()',
  'Cross-Origin-Embedder-Policy': 'require-corp',
  'Cross-Origin-Opener-Policy': 'same-origin',
  'Cross-Origin-Resource-Policy': 'same-origin'
};

// Security headers configuration with enhanced CSP
const securityHeaders = {
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'X-XSS-Protection': '1; mode=block',
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
  'Content-Security-Policy': getEnhancedCSP(),
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()',
  'Cross-Origin-Embedder-Policy': 'require-corp',
  'Cross-Origin-Opener-Policy': 'same-origin',
  'Cross-Origin-Resource-Policy': 'same-origin'
};

// Enhanced CSP policy generator
function getEnhancedCSP() {
  const frontendUrl = process.env.FRONTEND_URL || 'http://localhost:3001';
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const isProduction = process.env.NODE_ENV === 'production';

  const policies = [
    "default-src 'self'",
    "script-src 'self'" + (isProduction ? "" : ` ${frontendUrl}`), // Removed unsafe-inline/unsafe-eval
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    "img-src 'self' data: blob: https:",
    `connect-src 'self' ${apiUrl} ${frontendUrl} ws: wss: https://fonts.googleapis.com https://fonts.gstatic.com`,
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
  const reportUri = process.env.CSP_REPORT_URI || '/api/security/csp-violation';
  policies.push(`report-uri ${reportUri}`);

  return policies.join('; ');
}

// Rate limiting configuration
const rateLimitConfig = {
  global: false,
  max: 100, // 100 requests
  timeWindow: '1 minute',
  skipOnError: true,
  keyGenerator: (req) => {
    return req.headers['x-forwarded-for'] ||
           req.headers['x-real-ip'] ||
           req.ip ||
           req.connection.remoteAddress;
  },
  errorResponseBuilder: (req, context) => {
    return {
      statusCode: 429,
      error: 'Too Many Requests',
      message: `Rate limit exceeded. Try again later.`,
      retryAfter: context.after
    };
  }
};

// JWT configuration
const jwtConfig = {
  secret: process.env.JWT_SECRET || process.env.JWT_SECRET_KEY || 'fallback_jwt_secret_change_in_production',
  sign: {
    expiresIn: '1h'
  },
  verify: {
    maxAge: '1h'
  }
};

// API key validation
async function validateApiKey(request, reply) {
  const apiKey = request.headers['x-api-key'];

  if (!apiKey) {
    reply.code(401);
    return { error: 'API key required' };
  }

  // In production, validate against database or secure store
  const validApiKeys = [
    process.env.DEV_API_KEY,
    process.env.PROD_API_KEY,
    process.env.API_KEY_SECRET,
    process.env.CARTRITA_API_KEY
  ].filter(Boolean);

  if (!validApiKeys.length) {
    reply.code(500);
    return { error: 'Server configuration error: No API keys configured' };
  }

  if (!validApiKeys.includes(apiKey)) {
    reply.code(403);
    return { error: 'Invalid API key' };
  }
}

// Request sanitization
function sanitizeRequest(request) {
  // Remove sensitive headers
  const sensitiveHeaders = [
    'authorization',
    'x-api-key',
    'cookie',
    'x-auth-token'
  ];

  const sanitized = { ...request };
  sensitiveHeaders.forEach(header => {
    if (sanitized.headers && sanitized.headers[header]) {
      sanitized.headers[header] = '[REDACTED]';
    }
  });

  return sanitized;
}

// Input validation using Joi
function createValidationSchema(type) {
  const validationSchemas = {
    chatRequest: Joi.object({
      message: Joi.string().min(1).max(10000).required(),
      context: Joi.object().optional(),
      agentOverride: Joi.string().valid('research', 'code', 'computer_use', 'knowledge', 'task').optional(),
      stream: Joi.boolean().optional()
    })
  };
  return validationSchemas[type];
}

// Input validation middleware
async function validateInput(request, reply, schemaType) {
  try {
    const schema = createValidationSchema(schemaType);
    if (schema) {
      const { error } = schema.validate(request.body);
      if (error) {
        reply.code(400);
        return {
          error: 'Validation error',
          details: error.details.map(d => d.message)
        };
      }
    }
  } catch (validationError) {
    reply.code(400);
    return { error: 'Invalid request format' };
  }
}

// CORS configuration with strict origin validation
const corsConfig = {
  origin: (origin, callback) => {
    // Load allowed origins from environment variables
    const envOrigins = process.env.ALLOWED_ORIGINS
      ? process.env.ALLOWED_ORIGINS.split(',').map(o => o.trim())
      : [];

    const allowedOrigins = [
      'http://localhost:3000',
      'http://localhost:3001',
      'http://localhost:3003', // Turbopack dev server
      'https://cartrita.ai',
      'https://cartrita-ai-os.com',
      process.env.FRONTEND_URL,
      process.env.PRODUCTION_FRONTEND_URL,
      ...envOrigins
    ].filter(Boolean);

    // Allow requests with no origin (same-origin requests)
    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      console.warn(`CORS policy violation: Origin ${origin} not allowed`);
      callback(new Error('CORS policy violation'));
    }
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Api-Key', 'X-Request-ID']
};

// Check if request is from localhost/development
function isLocalhost(hostname) {
  return hostname === 'localhost' ||
         hostname === '127.0.0.1' ||
         hostname.startsWith('192.168.') ||
         hostname.startsWith('10.') ||
         hostname.startsWith('172.');
}

// HTTPS enforcement middleware
function enforceHTTPS(request, reply, done) {
  const forceHTTPS = process.env.NODE_ENV === 'production' || process.env.ENVIRONMENT === 'production';
  const isHTTPS = request.headers['x-forwarded-proto'] === 'https' || request.protocol === 'https';

  // Only enforce in production and if not already HTTPS
  if (forceHTTPS && !isHTTPS && !isLocalhost(request.hostname)) {
    const httpsUrl = `https://${request.hostname}${request.originalUrl || request.url}`;
    reply.code(301).redirect(httpsUrl);
    return;
  }

  done();
}

module.exports = {
  inputSchemas,
  securityHeaders,
  rateLimitConfig,
  jwtConfig,
  validateApiKey,
  sanitizeRequest,
  validateInput,
  corsConfig,
  enforceHTTPS
};
