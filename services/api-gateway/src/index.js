const fastify = require('fastify')({ logger: true });
require('dotenv').config();

const PORT = process.env.API_GATEWAY_PORT || 3000;
const HOST = '0.0.0.0';

// Register CORS
fastify.register(require('@fastify/cors'), {
  origin: true
});

// Register Helmet for security
fastify.register(require('@fastify/helmet'));

// Health check endpoint
fastify.get('/health', async (request, reply) => {
  return { status: 'OK', timestamp: new Date().toISOString() };
});

// Default route
fastify.get('/', async (request, reply) => {
  return { 
    message: 'Cartrita AI OS - API Gateway',
    version: '2.0.0',
    status: 'running'
  };
});

// Proxy to AI Orchestrator
fastify.register(async function (fastify) {
  const aiOrchestratorUrl = process.env.AI_ORCHESTRATOR_URL || 'http://ai-orchestrator:8000';
  
  fastify.all('/api/*', async (request, reply) => {
    const axios = require('axios');
    const path = request.url.replace('/api', '');
    const url = `${aiOrchestratorUrl}${path}`;
    
    try {
      const response = await axios({
        method: request.method,
        url: url,
        data: request.body,
        headers: {
          ...request.headers,
          host: undefined, // Remove host header
        },
        params: request.query,
      });
      
      reply.code(response.status);
      return response.data;
    } catch (error) {
      if (error.response) {
        reply.code(error.response.status);
        return error.response.data;
      } else {
        reply.code(500);
        return { error: 'Proxy error', message: error.message };
      }
    }
  });
});

// Start server
const start = async () => {
  try {
    await fastify.listen({ port: PORT, host: HOST });
    fastify.log.info(`🚀 API Gateway started on http://${HOST}:${PORT}`);
  } catch (err) {
    fastify.log.error(err);
    process.exit(1);
  }
};

start();