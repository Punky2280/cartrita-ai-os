/* eslint-env jest, node */
const {
  validateApiKey,
  sanitizeRequest,
  validateInput,
  corsConfig,
  securityHeaders,
  rateLimitConfig
} = require('../security');

describe('Security Middleware Tests', () => {
  describe('validateApiKey', () => {
    const mockRequest = {
      headers: {}
    };
    const mockReply = {
      code: jest.fn().mockReturnThis(),
      send: jest.fn()
    };

    beforeEach(() => {
      jest.clearAllMocks();
      process.env.DEV_API_KEY = 'dev-key-12345678901234567890123456';
      process.env.PROD_API_KEY = 'prod-key-12345678901234567890123456';
    });

    afterEach(() => {
      delete process.env.DEV_API_KEY;
      delete process.env.PROD_API_KEY;
    });

    test('should reject request without API key', async () => {
      const result = await validateApiKey(mockRequest, mockReply);

      expect(mockReply.code).toHaveBeenCalledWith(401);
      expect(result).toEqual({ error: 'API key required' });
    });

    test('should reject request with invalid API key', async () => {
      mockRequest.headers['x-api-key'] = 'invalid-key';

      const result = await validateApiKey(mockRequest, mockReply);

      expect(mockReply.code).toHaveBeenCalledWith(403);
      expect(result).toEqual({ error: 'Invalid API key' });
    });

    test('should accept request with valid dev API key', async () => {
      mockRequest.headers['x-api-key'] = 'dev-key-12345678901234567890123456';

      const result = await validateApiKey(mockRequest, mockReply);

      expect(mockReply.code).not.toHaveBeenCalled();
      expect(result).toBeUndefined();
    });

    test('should accept request with valid prod API key', async () => {
      mockRequest.headers['x-api-key'] = 'prod-key-12345678901234567890123456';

      const result = await validateApiKey(mockRequest, mockReply);

      expect(mockReply.code).not.toHaveBeenCalled();
      expect(result).toBeUndefined();
    });
  });

  describe('sanitizeRequest', () => {
    test('should redact sensitive headers', () => {
      const request = {
        headers: {
          'authorization': 'Bearer token123',
          'x-api-key': 'secret-key',
          'cookie': 'session=abc123',
          'x-auth-token': 'auth-token',
          'content-type': 'application/json'
        },
        body: { data: 'test' }
      };

      const sanitized = sanitizeRequest(request);

      expect(sanitized.headers.authorization).toBe('[REDACTED]');
      expect(sanitized.headers['x-api-key']).toBe('[REDACTED]');
      expect(sanitized.headers.cookie).toBe('[REDACTED]');
      expect(sanitized.headers['x-auth-token']).toBe('[REDACTED]');
      expect(sanitized.headers['content-type']).toBe('application/json');
      expect(sanitized.body).toEqual({ data: 'test' });
    });

    test('should handle request without headers', () => {
      const request = { body: { data: 'test' } };
      const sanitized = sanitizeRequest(request);

      expect(sanitized).toEqual({ body: { data: 'test' } });
    });
  });

  describe('validateInput', () => {
    const mockReply = {
      code: jest.fn().mockReturnThis(),
      send: jest.fn()
    };

    beforeEach(() => {
      jest.clearAllMocks();
    });

    test('should validate chatRequest successfully', async () => {
      const mockRequest = {
        body: {
          message: 'Hello world',
          context: { user_id: '123' },
          stream: true
        }
      };

      const result = await validateInput(mockRequest, mockReply, 'chatRequest');

      expect(mockReply.code).not.toHaveBeenCalled();
      expect(result).toBeUndefined();
    });

    test('should reject chatRequest without message', async () => {
      const mockRequest = {
        body: {
          context: { user_id: '123' }
        }
      };

      const result = await validateInput(mockRequest, mockReply, 'chatRequest');

      expect(mockReply.code).toHaveBeenCalledWith(400);
      expect(result.error).toBe('Validation error');
      expect(result.details).toContain('"message" is required');
    });

    test('should reject chatRequest with message too long', async () => {
      const mockRequest = {
        body: {
          message: 'a'.repeat(10001) // Exceeds max length of 10000
        }
      };

      const result = await validateInput(mockRequest, mockReply, 'chatRequest');

      expect(mockReply.code).toHaveBeenCalledWith(400);
      expect(result.error).toBe('Validation error');
      expect(result.details.some(d => d.includes('length'))).toBe(true);
    });

    test('should reject chatRequest with invalid agent_override', async () => {
      const mockRequest = {
        body: {
          message: 'Hello',
          agent_override: 'invalid_agent'
        }
      };

      const result = await validateInput(mockRequest, mockReply, 'chatRequest');

      expect(mockReply.code).toHaveBeenCalledWith(400);
      expect(result.error).toBe('Validation error');
    });

    test('should handle malformed request body', async () => {
      const mockRequest = {
        body: null
      };

      const result = await validateInput(mockRequest, mockReply, 'chatRequest');

      expect(mockReply.code).toHaveBeenCalledWith(400);
      expect(result).toEqual({ error: 'Invalid request format' });
    });
  });

  describe('corsConfig', () => {
    test('should allow localhost origins', (done) => {
      const callback = jest.fn((err, allowed) => {
        expect(err).toBe(null);
        expect(allowed).toBe(true);
        done();
      });

      corsConfig.origin('http://localhost:3000', callback);
    });

    test('should allow production domain', (done) => {
      const callback = jest.fn((err, allowed) => {
        expect(err).toBe(null);
        expect(allowed).toBe(true);
        done();
      });

      corsConfig.origin('https://cartrita.ai', callback);
    });

    test('should reject unauthorized origins', (done) => {
      const callback = jest.fn((err, allowed) => {
        expect(err.message).toBe('CORS policy violation');
        expect(allowed).toBeUndefined();
        done();
      });

      corsConfig.origin('https://malicious-site.com', callback);
    });

    test('should allow no origin (for same-origin requests)', (done) => {
      const callback = jest.fn((err, allowed) => {
        expect(err).toBe(null);
        expect(allowed).toBe(true);
        done();
      });

      corsConfig.origin(null, callback);
    });

    test('should use environment FRONTEND_URL when set', (done) => {
      process.env.FRONTEND_URL = 'https://custom-domain.com';

      const callback = jest.fn((err, allowed) => {
        expect(err).toBe(null);
        expect(allowed).toBe(true);
        delete process.env.FRONTEND_URL;
        done();
      });

      corsConfig.origin('https://custom-domain.com', callback);
    });
  });

  describe('Security Headers', () => {
    test('should include all required security headers', () => {
      expect(securityHeaders).toHaveProperty('X-Content-Type-Options', 'nosniff');
      expect(securityHeaders).toHaveProperty('X-Frame-Options', 'DENY');
      expect(securityHeaders).toHaveProperty('X-XSS-Protection', '1; mode=block');
      expect(securityHeaders).toHaveProperty('Strict-Transport-Security');
      expect(securityHeaders).toHaveProperty('Content-Security-Policy');
    });

    test('should have proper CSP policy', () => {
      const csp = securityHeaders['Content-Security-Policy'];
      expect(csp).toContain("default-src 'self'");
      expect(csp).toContain("script-src 'self' 'unsafe-inline'");
      expect(csp).toContain("style-src 'self' 'unsafe-inline'");
    });
  });

  describe('Rate Limit Configuration', () => {
    test('should have proper rate limit settings', () => {
      expect(rateLimitConfig.max).toBe(100);
      expect(rateLimitConfig.timeWindow).toBe('1 minute');
      expect(rateLimitConfig.skipOnError).toBe(true);
    });

    test('should extract client IP correctly', () => {
      const mockReq = {
        headers: {
          'x-forwarded-for': '192.168.1.1',
          'x-real-ip': '192.168.1.2'
        },
        ip: '192.168.1.3',
        connection: {
          remoteAddress: '192.168.1.4'
        }
      };

      const clientIp = rateLimitConfig.keyGenerator(mockReq);
      expect(clientIp).toBe('192.168.1.1'); // Should prefer x-forwarded-for
    });

    test('should fallback to other IP sources', () => {
      const mockReq = {
        headers: {},
        ip: '192.168.1.3',
        connection: {
          remoteAddress: '192.168.1.4'
        }
      };

      const clientIp = rateLimitConfig.keyGenerator(mockReq);
      expect(clientIp).toBe('192.168.1.3'); // Should fallback to req.ip
    });

    test('should create proper error response', () => {
      const mockReq = {};
      const mockContext = { after: 60 };

      const response = rateLimitConfig.errorResponseBuilder(mockReq, mockContext);

      expect(response.statusCode).toBe(429);
      expect(response.error).toBe('Too Many Requests');
      expect(response.retryAfter).toBe(60);
    });
  });

  describe('XSS Prevention', () => {
    test('should block messages with script tags', async () => {
      const mockRequest = {
        body: {
          message: '<script>alert("xss")</script>Hello'
        }
      };
      const mockReply = {
        code: jest.fn().mockReturnThis(),
        send: jest.fn()
      };

      const result = await validateInput(mockRequest, mockReply, 'chatRequest');

      expect(mockReply.code).toHaveBeenCalledWith(400);
      expect(result.error).toBe('Validation error');
    });

    test('should allow safe HTML entities', async () => {
      const mockRequest = {
        body: {
          message: 'Hello &amp; welcome to our service!'
        }
      };
      const mockReply = {
        code: jest.fn().mockReturnThis(),
        send: jest.fn()
      };

      const result = await validateInput(mockRequest, mockReply, 'chatRequest');

      expect(mockReply.code).not.toHaveBeenCalled();
      expect(result).toBeUndefined();
    });
  });
});

describe('Integration Tests', () => {
  test('should handle complete security workflow', async () => {
    // Simulate a complete request with all security measures
    const mockRequest = {
      headers: {
        'x-api-key': 'dev-key-12345678901234567890123456',
        'authorization': 'Bearer token123',
        'origin': 'http://localhost:3000'
      },
      body: {
        message: 'Hello, how are you?',
        context: { session_id: 'abc123' },
        stream: false
      }
    };
    const mockReply = {
      code: jest.fn().mockReturnThis(),
      send: jest.fn()
    };

    // Set environment variables
    process.env.DEV_API_KEY = 'dev-key-12345678901234567890123456';

    try {
      // Test API key validation
      const apiKeyResult = await validateApiKey(mockRequest, mockReply);
      expect(apiKeyResult).toBeUndefined();

      // Test input validation
      const inputResult = await validateInput(mockRequest, mockReply, 'chatRequest');
      expect(inputResult).toBeUndefined();

      // Test request sanitization
      const sanitized = sanitizeRequest(mockRequest);
      expect(sanitized.headers.authorization).toBe('[REDACTED]');
      expect(sanitized.headers['x-api-key']).toBe('[REDACTED]');

      // Test CORS validation
      const corsCallback = jest.fn();
      corsConfig.origin(mockRequest.headers.origin, corsCallback);
      expect(corsCallback).toHaveBeenCalledWith(null, true);

    } finally {
      delete process.env.DEV_API_KEY;
    }
  });
});
