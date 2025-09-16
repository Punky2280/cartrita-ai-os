const fastify = require('fastify')({
  logger: true,
  trustProxy: true,
  requestIdHeader: 'x-request-id',
  requestIdLogLabel: 'reqId',
  bodyLimit: 1048576 // 1MB limit
});
require('dotenv').config();
const proxy = require('@fastify/http-proxy');
const promClient = require('prom-client');
const {
  schemas,
  securityHeaders,
  rateLimitConfig,
  jwtConfig,
  validateApiKey,
  corsConfig
} = require('./middleware/security');

const PORT = process.env.API_GATEWAY_PORT || 3000;
const HOST = '0.0.0.0';

// Register CORS with strict configuration
fastify.register(require('@fastify/cors'), corsConfig);

// Register rate limiting
fastify.register(require('@fastify/rate-limit'), rateLimitConfig);

// Register JWT
fastify.register(require('@fastify/jwt'), jwtConfig);

// Add security headers to all responses
fastify.addHook('onSend', (request, reply, payload, done) => {
  Object.entries(securityHeaders).forEach(([key, value]) => {
    reply.header(key, value);
  });
  done();
});

// Register Helmet for security (will be registered in start function)

// --------------------------------------------------
// Health & Metrics
// --------------------------------------------------
fastify.get('/health', async () => ({ status: 'OK', timestamp: new Date().toISOString() }));

// Prometheus metrics setup
const collectDefaultMetrics = promClient.collectDefaultMetrics;
collectDefaultMetrics();
const gatewayRequests = new promClient.Counter({
  name: 'gateway_requests_total',
  help: 'Total number of requests received by the API gateway',
  labelNames: ['method', 'route', 'status']
});

fastify.addHook('onResponse', (req, reply, done) => {
  try {
    const route = (req.routeOptions && req.routeOptions.url) || req.url;
    gatewayRequests.inc({ method: req.method, route, status: reply.statusCode });
  } catch (_) { /* swallow metrics errors */ }
  done();
});

fastify.get('/metrics', async (request, reply) => {
  try {
    reply.header('Content-Type', promClient.register.contentType);
    return await promClient.register.metrics();
  } catch (err) {
    reply.code(500);
    return `# metrics collection error\n${err.message}`;
  }
});

// Default route (non-frontend root informational JSON)
fastify.get('/', async () => ({
  message: 'Cartrita AI OS - API Gateway',
  version: '2.0.0',
  status: 'running'
}));

// --------------------------------------------------
// Proxy Configuration
// --------------------------------------------------
fastify.register(async function (fastify) {
  const aiOrchestratorUrl = process.env.AI_ORCHESTRATOR_URL || 'http://ai-orchestrator:8000';
  const frontendInternal = process.env.FRONTEND_INTERNAL_URL || 'http://frontend:3000';

  // API → Orchestrator proxy with authentication and validation
  fastify.all('/api/*', {
    preHandler: async (request, reply) => {
      // Validate API key for protected endpoints
      if (!request.url.includes('/health') && !request.url.includes('/metrics')) {
        const apiKey = request.headers['x-api-key'];
        if (!apiKey || !process.env.DEV_API_KEY || apiKey !== process.env.DEV_API_KEY) {
          reply.code(401);
          reply.send({ error: 'Unauthorized' });
          return;
        }
      }
    }
  }, async (request, reply) => {
    const axios = require('axios');
    const rawPath = request.url.replace('/api', '');
    // Enhanced SSRF protection and input validation
    if (rawPath.includes('://') || rawPath.startsWith('//') || rawPath.includes('..')) {
      reply.code(400);
      return { error: 'Invalid path' };
    }

    // Validate request body for POST/PUT requests
    if (['POST', 'PUT', 'PATCH'].includes(request.method) && request.body) {
      // Size check
      const bodySize = JSON.stringify(request.body).length;
      if (bodySize > 1048576) { // 1MB limit
        reply.code(413);
        return { error: 'Request body too large' };
      }

      // Content validation for chat endpoints
      if (request.url.includes('/chat') && request.body.message) {
        if (request.body.message.length > 10000) {
          reply.code(400);
          return { error: 'Message too long' };
        }
      }
    }
    const base = new URL(aiOrchestratorUrl);
    const target = new URL(rawPath, base);
    if (target.origin !== base.origin) {
      reply.code(400);
      return { error: 'Disallowed target origin' };
    }
    try {
      const headers = { ...request.headers };
      delete headers.host;
      delete headers['x-forwarded-host'];
      delete headers['x-forwarded-proto'];
      delete headers['x-forwarded-for'];

      // Avoid sending user-controlled absolute URLs to the HTTP client
      const pathOnly = target.pathname;

      const response = await axios({
        method: request.method,
        baseURL: base.origin,
        url: pathOnly,
        data: request.body,
        headers,
        params: request.query,
        timeout: 30000, // 30 second timeout
        maxContentLength: 10485760, // 10MB response limit
        validateStatus: (status) => status < 500 // Don't throw on 4xx
      });
      reply.code(response.status);
      return response.data;
    } catch (error) {
      // Enhanced error handling with logging
      fastify.log.error({
        error: error.message,
        path: rawPath,
        method: request.method
      });

      if (error.response) {
        reply.code(error.response.status);
        return error.response.data;
      }

      if (error.code === 'ECONNABORTED') {
        reply.code(504);
        return { error: 'Gateway timeout' };
      }

      reply.code(502);
      return { error: 'Service unavailable' };
    }
  });

  // Next.js asset & HMR proxying
  // Static/_next assets & HMR
  await fastify.register(proxy, {
    upstream: frontendInternal,
    prefix: '/_next',
    rewritePrefix: '/_next'
  });

  // Service worker (if present)
  await fastify.register(proxy, {
    upstream: frontendInternal,
    prefix: '/sw.js',
    rewritePrefix: '/sw.js'
  });

  // Fallback HTML (SSR / SPA) via notFound handler to avoid OPTIONS conflicts
  fastify.setNotFoundHandler(async (request, reply) => {
    if (request.url.startsWith('/api')) {
      reply.code(404);
      return { error: 'Not found' };
    }
    const undici = await import('undici');
    const target = `${frontendInternal}${request.url}`;
    try {
      const proxied = await undici.request(target, {
        method: request.method,
        headers: request.headers,
        body:
          request.body && request.headers['content-type'] &&
          request.headers['content-type'].includes('application/json')
            ? JSON.stringify(request.body)
            : undefined
      });
      reply.code(proxied.statusCode);
      // Filter out hop-by-hop headers per RFC 7230 section 6.1
      const hopByHopHeaders = [
        'connection',
        'keep-alive',
        'proxy-authenticate',
        'proxy-authorization',
        'te',
        'trailer',
        'transfer-encoding',
        'upgrade'
      ];
      for (const [h, v] of Object.entries(proxied.headers)) {
        if (!hopByHopHeaders.includes(h.toLowerCase())) {
          reply.header(h, v);
        }
      }
      return proxied.body;
    } catch (e) {
      reply.code(502);
      return { error: 'Frontend proxy failed', message: e.message };
    }
  });
});

// Start server
const start = async () => {
  try {
    // Register Helmet for security
    await fastify.register((await import('@fastify/helmet')).default);

    await fastify.listen({ port: PORT, host: HOST });
    fastify.log.info(`🚀 API Gateway started on http://${HOST}:${PORT}`);
  } catch (err) {
    fastify.log.error(err);
    process.exit(1);
  }
};

start();
