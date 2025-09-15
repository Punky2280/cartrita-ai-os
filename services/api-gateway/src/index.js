const fastify = require('fastify')({ logger: true });
require('dotenv').config();
const proxy = require('@fastify/http-proxy');
const promClient = require('prom-client');

const PORT = process.env.API_GATEWAY_PORT || 3000;
const HOST = '0.0.0.0';

// Register CORS
fastify.register(require('@fastify/cors'), { origin: true });

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

  // API → Orchestrator proxy (retain existing axios logic for flexibility)
  fastify.all('/api/*', async (request, reply) => {
    const axios = require('axios');
    const rawPath = request.url.replace('/api', '');
    // Basic SSRF hardening: disallow absolute/authority-form URLs and ensure same-origin target
    if (rawPath.includes('://') || rawPath.startsWith('//')) {
      reply.code(400);
      return { error: 'Invalid path' };
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
        params: request.query
      });
      reply.code(response.status);
      return response.data;
    } catch (error) {
      if (error.response) {
        reply.code(error.response.status);
        return error.response.data;
      }
      reply.code(500);
      return { error: 'Proxy error', message: error.message };
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
