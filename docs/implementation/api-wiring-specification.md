# Cartrita AI OS - API Wiring Specification

## Overview
This document specifies the API wiring between frontend and backend components, including authentication, streaming, and multi-provider support.

## Authentication Strategy

### API Key Management
- Frontend injects provider-specific API keys via `X-API-Key` header
- Backend validates keys per provider endpoint
- Secure key rotation and storage mechanisms

### Provider Mapping
```typescript
const providerMapping = {
  chat: 'openai',           // Default for chat endpoints
  huggingface: 'huggingface', // HuggingFace-specific endpoints
  voice: 'deepgram',        // Voice processing
  search: 'tavily',         // Search functionality
  github: 'github'          // GitHub integration
};
```

## Frontend API Client

### CartritaApiClient Class
```typescript
export class CartritaApiClient {
  private client: AxiosInstance;
  private baseURL: string;

  constructor(baseURL: string = '/api') {
    this.baseURL = baseURL;
    this.setupClient();
  }

  private setupClient() {
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for API key injection
    this.client.interceptors.request.use((config) => {
      const provider = this.extractProviderFromUrl(config.url || '');
      if (provider) {
        const apiKey = this.getApiKey(provider);
        if (apiKey) {
          config.headers['X-API-Key'] = apiKey;
        }
      }
      return config;
    });
  }

  private extractProviderFromUrl(url: string): string | null {
    if (url.includes('/chat')) return 'openai';
    if (url.includes('/huggingface')) return 'huggingface';
    if (url.includes('/voice')) return 'deepgram';
    if (url.includes('/search')) return 'tavily';
    if (url.includes('/github')) return 'github';
    return null;
  }

  private getApiKey(provider: string): string {
    const keys = {
      openai: process.env.NEXT_PUBLIC_OPENAI_API_KEY,
      huggingface: process.env.NEXT_PUBLIC_HUGGINGFACE_API_KEY,
      deepgram: process.env.NEXT_PUBLIC_DEEPGRAM_API_KEY,
      tavily: process.env.NEXT_PUBLIC_TAVILY_API_KEY,
      github: process.env.NEXT_PUBLIC_GITHUB_API_KEY,
    };
    return keys[provider as keyof typeof keys] || '';
  }
}
```

### Chat Methods
```typescript
// Regular chat
async postChat(request: ChatRequest): Promise<ChatResponse> {
  const response = await this.client.post('/chat', request);
  return response.data;
}

// Streaming chat
async streamChat(request: ChatRequest): Promise<EventSource> {
  const params = new URLSearchParams();
  Object.entries(request).forEach(([key, value]) => {
    if (value !== undefined) {
      params.append(key, String(value));
    }
  });

  return new EventSource(`${this.baseURL}/chat/stream?${params}`);
}
```

### Agent Discovery
```typescript
async getAgents(): Promise<AgentInfo[]> {
  const response = await this.client.get('/agents');
  return response.data.agents;
}
```

### File Operations
```typescript
async uploadFile(file: File, conversationId?: string): Promise<FileUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  if (conversationId) {
    formData.append('conversation_id', conversationId);
  }

  const response = await this.client.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
}
```

### Search Integration
```typescript
async search(query: string, provider: string = 'tavily'): Promise<SearchResponse> {
  const response = await this.client.post('/search', { query, provider });
  return response.data;
}
```

### Voice Processing
```typescript
async processVoice(audio: Blob): Promise<VoiceInputResponse> {
  const formData = new FormData();
  formData.append('audio', audio);

  const response = await this.client.post('/voice/process', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
}
```

### Computer Use
```typescript
async executeComputerTask(request: ComputerUseRequest): Promise<ComputerUseResponse> {
  const response = await this.client.post('/computer-use/execute', request);
  return response.data;
}
```

## Backend API Endpoints

### Chat Endpoints
```python
@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    api_key: str = Depends(validate_api_key)
):
    """Handle chat requests with multi-provider support"""
    try:
        logger.info("Processing chat request", conversation_id=request.conversation_id)

        # Route to appropriate provider based on request
        if request.provider == "openai":
            response = await handle_openai_chat(request)
        elif request.provider == "huggingface":
            response = await handle_huggingface_chat(request)
        else:
            # Default to orchestrator logic
            response = await handle_orchestrated_chat(request)

        return response
    except Exception as e:
        logger.error("Chat endpoint error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
```

### Streaming Endpoints
```python
@app.post("/api/chat/stream")
async def chat_stream_endpoint(
    request: ChatRequest,
    api_key: str = Depends(validate_api_key)
):
    """Handle streaming chat requests"""
    async def generate():
        try:
            async for chunk in stream_chat_response(request):
                yield f"data: {chunk}\n\n"
        except Exception as e:
            logger.error("Streaming error", error=str(e))
            yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )
```

### Agent Discovery
```python
@app.get("/api/agents", response_model=AgentDiscovery)
async def list_agents(api_key: str = Depends(validate_api_key)):
    """List available agents"""
    try:
        agents = await get_available_agents()
        return AgentDiscovery(agents=agents, total=len(agents))
    except Exception as e:
        logger.error("List agents error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
```

### WebSocket Support
```python
@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Process WebSocket messages for real-time communication
            await websocket.send_text(f"Echo: {data}")
    except Exception as e:
        logger.error("WebSocket error", error=str(e))
```

## Streaming Architecture

### SSE (Server-Sent Events) - Primary
- Real-time updates for chat responses
- Event framing with metadata
- Automatic reconnection handling
- Fallback to WebSocket if SSE not supported

### WebSocket - Fallback
- Bidirectional communication
- Lower latency for real-time features
- Connection state management
- Message queuing during disconnection

## Error Handling

### Frontend Error Handling
```typescript
this.client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle authentication errors
      this.handleAuthError();
    } else if (error.response?.status === 429) {
      // Handle rate limiting
      this.handleRateLimit();
    } else {
      // Handle other errors
      this.handleGenericError(error);
    }
    return Promise.reject(error);
  }
);
```

### Backend Error Handling
```python
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
```

## Rate Limiting

### Per-Provider Limits
- OpenAI: 100 requests/minute
- HuggingFace: 200 requests/minute
- Deepgram: 30 requests/minute
- Tavily: 100 requests/minute
- GitHub: 500 requests/hour

### Burst Handling
- Burst multiplier: 2x base rate
- Queue strategy: FIFO
- Timeout: 30 seconds

## Monitoring Integration

### Langfuse Integration
```python
from langfuse import Langfuse

langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST")
)

# Track API calls
with langfuse.trace() as trace:
    trace.set_input(request)
    response = await process_request(request)
    trace.set_output(response)
```

### Metrics Collection
- Response times per provider
- Error rates by endpoint
- Token usage tracking
- User session analytics

## Security Considerations

### API Key Security
- Environment variable storage
- No logging of API keys
- Key rotation mechanisms
- Provider-specific validation

### Input Validation
- Comprehensive schema validation
- File upload size limits
- Content type restrictions
- XSS prevention

### CORS Configuration
- Origin validation
- Credential handling
- Preflight request support

## Performance Optimization

### Caching Strategy
- Response caching for identical requests
- Model output caching
- Static asset optimization
- CDN integration

### Connection Pooling
- Database connection pooling
- HTTP client connection reuse
- WebSocket connection management

### Load Balancing
- Round-robin distribution
- Health check monitoring
- Auto-scaling triggers

## Testing Strategy

### Unit Tests
```typescript
describe('CartritaApiClient', () => {
  it('should create instance correctly', () => {
    const client = new CartritaApiClient();
    expect(client).toBeInstanceOf(CartritaApiClient);
  });

  it('should handle chat request', async () => {
    // Mock implementation
  });
});
```

### Integration Tests
```python
def test_chat_endpoint():
    response = client.post("/api/chat", json={
        "message": "Hello",
        "provider": "openai"
    })
    assert response.status_code == 200
    assert "response" in response.json()
```

### Load Tests
- Concurrent user simulation
- Peak load testing
- Memory leak detection
- Performance benchmarking

## Deployment Considerations

### Environment Configuration
```bash
# Required environment variables
OPENAI_API_KEY=sk-...
HUGGINGFACE_API_KEY=hf_...
DEEPGRAM_API_KEY=...
TAVILY_API_KEY=...
GITHUB_API_KEY=...
```

### Container Configuration
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
```

### Health Checks
```typescript
// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    version: process.env.npm_package_version
  });
});
```

This specification provides a comprehensive blueprint for implementing the API wiring between frontend and backend components with proper authentication, streaming, error handling, and monitoring integration.
