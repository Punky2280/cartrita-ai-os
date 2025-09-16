/* eslint-env node */
const Joi = require('joi');
const redis = require('redis');

// Input validation schemas
const schemas = {
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
      agent_override: {
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

// Security headers configuration
const securityHeaders = {
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'X-XSS-Protection': '1; mode=block',
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
  'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
};

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
  secret: process.env.JWT_SECRET || 'change_this_to_a_secure_random_string',
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
    process.env.PROD_API_KEY
  ].filter(Boolean);

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
  const schemas = {
    chatRequest: Joi.object({
      message: Joi.string().min(1).max(10000).required(),
      context: Joi.object().optional(),
      agent_override: Joi.string().valid('research', 'code', 'computer_use', 'knowledge', 'task').optional(),
      stream: Joi.boolean().optional()
    })
  };
  return schemas[type];
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
  } catch (err) {
    reply.code(400);
    return { error: 'Invalid request format' };
  }
}

// CORS configuration with strict origin validation
const corsConfig = {
  origin: (origin, callback) => {
    const allowedOrigins = [
      'http://localhost:3000',
      'http://localhost:3001',
      'https://cartrita.ai',
      process.env.FRONTEND_URL
    ].filter(Boolean);

    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('CORS policy violation'));
    }
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Api-Key']
};

module.exports = {
  schemas,
  securityHeaders,
  rateLimitConfig,
  jwtConfig,
  validateApiKey,
  sanitizeRequest,
  validateInput,
  corsConfig
};
