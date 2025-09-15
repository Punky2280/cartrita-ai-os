// Cartrita AI OS - API Client
// Comprehensive API client for frontend-backend communication

import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  InternalAxiosRequestConfig,
} from "axios";
import { z } from "zod";
import type {
  User,
  Conversation,
  Message,
  Agent,
  ChatRequest,
  ChatResponse,
  ApiResponse,
  StreamingChunk,
  HealthStatus,
  MetricsData,
  SearchFilters,
  Plugin,
  Workspace,
  Notification,
  VoiceSettings,
  ThemeConfig,
  FileUploadResult,
} from "@/types";
import {
  createApiResponse,
  handleApiError,
  createStreamingChunk,
  logError,
} from "@/utils";

// SSE Event Types based on our schema
export type SSEEvent =
  | {
      event: "stream_start";
      data: { conversation_id: string };
      id?: string;
      retry?: number;
    }
  | {
      event: "token";
      data: { content: string; delta?: string };
      id?: string;
      retry?: number;
    }
  | {
      event: "function_call";
      data: { function_name: string; arguments: unknown };
      id?: string;
      retry?: number;
    }
  | {
      event: "tool_result";
      data: { tool_name: string; result: unknown };
      id?: string;
      retry?: number;
    }
  | {
      event: "agent_task_start";
      data: { task_id: string; agent_type: string; description: string };
      id?: string;
      retry?: number;
    }
  | {
      event: "agent_task_progress";
      data: { task_id: string; progress: number; status: string };
      id?: string;
      retry?: number;
    }
  | {
      event: "agent_task_complete";
      data: { task_id: string; result: unknown; success: boolean };
      id?: string;
      retry?: number;
    }
  | {
      event: "metrics";
      data: Record<string, unknown>;
      id?: string;
      retry?: number;
    }
  | {
      event: "error";
      data: { error: string; code?: string; recoverable?: boolean };
      id?: string;
      retry?: number;
    }
  | {
      event: "done";
      data: {
        final_response: string;
        conversation_id: string;
        agent_type?: string;
        processing_time?: number;
        token_usage?: unknown;
        sources?: unknown;
        message_id?: string;
      };
      id?: string;
      retry?: number;
    };

// Narrow helper
function isSSEEvent(value: unknown): value is SSEEvent {
  return (
    typeof value === "object" &&
    value !== null &&
    "event" in (value as any) &&
    "data" in (value as any)
  );
}

export interface StreamingCallbacks {
  onToken?: (content: string, delta?: string) => void;
  onFunctionCall?: (functionName: string, args: unknown) => void;
  onToolResult?: (toolName: string, result: unknown) => void;
  onAgentTaskStart?: (
    taskId: string,
    agentType: string,
    description: string,
  ) => void;
  onAgentTaskProgress?: (
    taskId: string,
    progress: number,
    status: string,
  ) => void;
  onAgentTaskComplete?: (
    taskId: string,
    result: unknown,
    success: boolean,
  ) => void;
  onMetrics?: (metrics: unknown) => void;
  onError?: (error: string, code: string, recoverable: boolean) => void;
  onDone?: (finalResponse: string, metadata: unknown) => void;
}

// WebSocket Message Types
export interface WebSocketMessage {
  type: "auth" | "chat" | "ping" | "pong";
  api_key?: string;
  message?: string;
  context?: Record<string, unknown>;
  conversation_id?: string;
}

// Extend AxiosRequestConfig to include metadata
declare module "axios" {
  interface AxiosRequestConfig {
    metadata?: {
      requestId: string;
      startTime: number;
    };
  }
}

// API Response Schemas for Runtime Validation
// Some legacy endpoints (e.g. /health) may not include `success`; we'll handle that gracefully.
const ApiResponseSchema = z.object({
  success: z.boolean().optional(),
  data: z.any().optional(),
  error: z.string().optional(),
  message: z.string().optional(),
  metadata: z
    .object({
      timestamp: z.string().optional(),
      version: z.string().optional(),
      requestId: z.string().optional(),
      processingTime: z.number().optional(),
    })
    .optional(),
});

// Health status schema reflecting backend expectations (success may be absent)
const HealthStatusSchema = z
  .object({
    status: z.enum(["healthy", "unhealthy", "degraded"]).optional(),
    version: z.string().optional(),
    uptime: z.number().optional(),
    timestamp: z.string().optional(),
    services: z.record(z.any()).optional(),
  })
  .passthrough();

const UserSchema = z.object({
  id: z.string(),
  email: z.string().email(),
  name: z.string(),
  avatar: z.string().optional(),
  preferences: z.object({
    theme: z.enum(["light", "dark", "system"]),
    language: z.string(),
    notifications: z.boolean(),
    autoSave: z.boolean(),
  }),
  createdAt: z.string(),
  updatedAt: z.string(),
  lastLoginAt: z.string().optional(),
  isActive: z.boolean(),
  role: z.enum(["user", "admin", "moderator"]),
});

const ConversationSchema = z.object({
  id: z.string(),
  title: z.string(),
  messages: z.array(z.any()), // Will be validated separately
  agentId: z.string().optional(),
  workspaceId: z.string().optional(),
  userId: z.string(),
  isArchived: z.boolean(),
  isPinned: z.boolean(),
  tags: z.array(z.string()),
  metadata: z.record(z.any()),
  createdAt: z.string(),
  updatedAt: z.string(),
  lastMessageAt: z.string().optional(),
});

const MessageSchema = z.object({
  id: z.string(),
  conversationId: z.string(),
  role: z.enum(["user", "assistant", "system"]),
  content: z.string(),
  attachments: z.array(z.any()).optional(),
  metadata: z.record(z.any()),
  createdAt: z.string(),
  updatedAt: z.string(),
  isEdited: z.boolean(),
  tokens: z.number().optional(),
  processingTime: z.number().optional(),
});

const AgentSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  type: z.string(),
  capabilities: z.array(z.string()),
  model: z.string(),
  parameters: z.record(z.any()),
  isActive: z.boolean(),
  createdAt: z.string(),
  updatedAt: z.string(),
  metrics: z.object({
    totalRequests: z.number(),
    successRate: z.number(),
    avgLatency: z.number(),
    lastActive: z.string(),
  }),
});

// Custom Error Classes
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public response?: unknown,
    public requestId?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export class NetworkError extends Error {
  constructor(
    message: string,
    public originalError?: unknown,
  ) {
    super(message);
    this.name = "NetworkError";
  }
}

export class ValidationError extends Error {
  constructor(
    message: string,
    public errors?: Record<string, string[]>,
  ) {
    super(message);
    this.name = "ValidationError";
  }
}

// Main API Client Class
export class CartritaApiClient {
  private client: AxiosInstance;
  private baseURL: string;
  private timeout: number;
  private retryCount: number;
  private requestQueue: Map<string, AbortController> = new Map();

  constructor(
    config: {
      baseURL?: string;
      timeout?: number;
      retryCount?: number;
      apiKey?: string;
    } = {},
  ) {
    this.baseURL = config.baseURL || process.env.NEXT_PUBLIC_API_URL || "/api";
    this.timeout = config.timeout || 30000;
    this.retryCount = config.retryCount || 3;

    // Get API key from multiple sources
    const apiKey =
      config.apiKey ||
      process.env.NEXT_PUBLIC_CARTRITA_API_KEY ||
      "dev-key-cartrita-ai-os";

    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: this.timeout,
      headers: {
        "Content-Type": "application/json",
        "X-Client-Version": "Cartrita-Client/2.0.0",
        // Support both header formats for compatibility
        "X-API-Key": apiKey,
        Authorization: `Bearer ${apiKey}`,
      },
    });

    this.setupInterceptors();
  }

  // Static method to create instance
  static createInstance(config?: {
    baseURL?: string;
    timeout?: number;
    retryCount?: number;
    apiKey?: string;
  }): CartritaApiClient {
    return new CartritaApiClient(config);
  }

  // Set authentication token
  setAuthToken(token: string): void {
    this.client.defaults.headers.common["Authorization"] = `Bearer ${token}`;
    this.client.defaults.headers.common["X-API-Key"] = token;
  }

  // Remove authentication token
  removeAuthToken(): void {
    delete this.client.defaults.headers.common["Authorization"];
    delete this.client.defaults.headers.common["X-API-Key"];
  }

  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        config.metadata = { requestId, startTime: Date.now() };

        // Add to request queue for cancellation
        const controller = new AbortController();
        config.signal = controller.signal;
        this.requestQueue.set(requestId, controller);

        return config;
      },
      (error) => {
        logError(error, { context: "request_interceptor" });
        return Promise.reject(error);
      },
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        const requestId = response.config.metadata?.requestId;
        if (requestId) {
          this.requestQueue.delete(requestId);
        }

        // Validate response structure
        try {
          // Attempt generic API response validation; tolerate health/status endpoints
          ApiResponseSchema.parse(response.data);
        } catch (validationError) {
          // Special-case: /health endpoint often returns a plain object without success flag
          if (response.config.url?.includes("/health")) {
            try {
              HealthStatusSchema.parse(response.data);
            } catch (healthErr) {
              logError(healthErr as Error, {
                context: "health_response_validation",
                requestId,
                url: response.config.url,
              });
            }
          } else {
            logError(validationError as Error, {
              context: "response_validation",
              requestId,
              url: response.config.url,
            });
          }
        }

        return response;
      },
      (error) => {
        const requestId = error.config?.metadata?.requestId;
        if (requestId) {
          this.requestQueue.delete(requestId);
        }

        if (error.code === "ECONNABORTED" || error.code === "ENOTFOUND") {
          return Promise.reject(
            new NetworkError("Network connection failed", error),
          );
        }

        if (error.response?.status === 422) {
          const validationErrors = error.response.data?.errors;
          return Promise.reject(
            new ValidationError("Validation failed", validationErrors),
          );
        }

        if (error.response) {
          return Promise.reject(
            new ApiError(
              error.response.status,
              error.response.data?.error || error.message,
              error.response.data,
              requestId,
            ),
          );
        }

        logError(error, { context: "response_interceptor", requestId });
        return Promise.reject(error);
      },
    );
  }

  // Generic request method with retry logic
  private async request<T>(
    method: "GET" | "POST" | "PUT" | "DELETE" | "PATCH",
    endpoint: string,
    data?: unknown,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<T>> {
    const requestConfig: AxiosRequestConfig = {
      method,
      url: endpoint,
      ...(data && { data }),
      ...config,
    };

    let lastError: unknown;

    for (let attempt = 1; attempt <= this.retryCount; attempt++) {
      try {
        const response: AxiosResponse<ApiResponse<T>> =
          await this.client.request(requestConfig);
        return response.data;
      } catch (error) {
        lastError = error;

        // Don't retry on client errors (4xx) except 429 (rate limit)
        if (
          error instanceof ApiError &&
          error.status >= 400 &&
          error.status < 500 &&
          error.status !== 429
        ) {
          break;
        }

        // Don't retry on the last attempt
        if (attempt === this.retryCount) {
          break;
        }

        // Exponential backoff
        const delay = Math.min(1000 * Math.pow(2, attempt - 1), 10000);
        await new Promise((resolve) => setTimeout(resolve, delay));
      }
    }

    throw lastError;
  }

  // Authentication methods
  async login(
    email: string,
    password: string,
  ): Promise<ApiResponse<{ user: User; token: string }>> {
    return this.request("POST", "/auth/login", { email, password });
  }

  async register(userData: {
    email: string;
    password: string;
    name: string;
  }): Promise<ApiResponse<{ user: User; token: string }>> {
    return this.request("POST", "/auth/register", userData);
  }

  async logout(): Promise<ApiResponse<void>> {
    return this.request("POST", "/auth/logout");
  }

  async refreshToken(): Promise<ApiResponse<{ token: string }>> {
    return this.request("POST", "/auth/refresh");
  }

  async getCurrentUser(): Promise<ApiResponse<User>> {
    const response = await this.request<User>("GET", "/auth/me");
    try {
      UserSchema.parse(response.data);
    } catch (error) {
      throw new ValidationError("Invalid user data received");
    }
    return response;
  }

  async updateUserPreferences(
    preferences: Partial<User["preferences"]>,
  ): Promise<ApiResponse<User>> {
    return this.request("PUT", "/auth/preferences", { preferences });
  }

  async updateThemeConfig(
    themeConfig: ThemeConfig,
  ): Promise<ApiResponse<User>> {
    return this.request("PUT", "/auth/theme", { themeConfig });
  }

  async updateVoiceSettings(
    voiceSettings: VoiceSettings,
  ): Promise<ApiResponse<User>> {
    return this.request("PUT", "/auth/voice", { voiceSettings });
  }

  // Conversation methods
  async getConversations(
    filters?: SearchFilters,
  ): Promise<ApiResponse<Conversation[]>> {
    const params = filters
      ? new URLSearchParams(filters as any).toString()
      : "";
    const endpoint = `/conversations${params ? `?${params}` : ""}`;
    return this.request("GET", endpoint);
  }

  async getConversation(id: string): Promise<ApiResponse<Conversation>> {
    const response = await this.request<Conversation>(
      "GET",
      `/conversations/${id}`,
    );
    try {
      ConversationSchema.parse(response.data);
    } catch (error) {
      throw new ValidationError("Invalid conversation data received");
    }
    return response;
  }

  async createConversation(data: {
    title?: string;
    agentId?: string;
    workspaceId?: string;
    initialMessage?: string;
  }): Promise<ApiResponse<Conversation>> {
    return this.request("POST", "/conversations", data);
  }

  async updateConversation(
    id: string,
    data: Partial<Pick<Conversation, "title" | "isArchived" | "tags">>,
  ): Promise<ApiResponse<Conversation>> {
    return this.request("PUT", `/conversations/${id}`, data);
  }

  async deleteConversation(id: string): Promise<ApiResponse<void>> {
    return this.request("DELETE", `/conversations/${id}`);
  }

  async archiveConversation(id: string): Promise<ApiResponse<Conversation>> {
    return this.request("PUT", `/conversations/${id}/archive`);
  }

  async pinConversation(id: string): Promise<ApiResponse<Conversation>> {
    return this.request("PUT", `/conversations/${id}/pin`);
  }

  // Message methods
  async getMessages(
    conversationId: string,
    params?: {
      limit?: number;
      offset?: number;
      before?: string;
      after?: string;
    },
  ): Promise<ApiResponse<Message[]>> {
    const queryParams = params
      ? new URLSearchParams(params as any).toString()
      : "";
    const endpoint = `/conversations/${conversationId}/messages${queryParams ? `?${queryParams}` : ""}`;
    const response = await this.request<Message[]>("GET", endpoint);

    // Validate each message
    if (Array.isArray(response.data)) {
      response.data.forEach((message, index) => {
        try {
          MessageSchema.parse(message);
        } catch (error) {
          logError(error as Error, {
            context: "message_validation",
            conversationId,
            messageIndex: index,
          });
        }
      });
    }

    return response;
  }

  async sendMessage(
    conversationId: string,
    message: ChatRequest,
  ): Promise<ApiResponse<ChatResponse>> {
    return this.request(
      "POST",
      `/conversations/${conversationId}/messages`,
      message,
    );
  }

  // New chat method that matches backend
  async postChat(request: ChatRequest): Promise<ApiResponse<ChatResponse>> {
    const response = await this.request<ChatResponse>("POST", "/chat", request);

    // Normalize backend response to frontend Message shape
    if (response.data) {
      const normalizedMessage: Message = {
        id: crypto.randomUUID(),
        conversationId: response.data.conversation_id as string,
        role: "assistant",
        content: response.data.response,
        attachments: [],
        metadata: response.data.metadata || {},
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        isEdited: false,
        tokens: response.data.token_usage?.total_tokens,
        processingTime: response.data.processing_time,
      };

      // Attach normalized message
      response.data.message = normalizedMessage;
    }

    return response;
  }

  async editMessage(
    conversationId: string,
    messageId: string,
    content: string,
  ): Promise<ApiResponse<Message>> {
    return this.request(
      "PUT",
      `/conversations/${conversationId}/messages/${messageId}`,
      { content },
    );
  }

  async deleteMessage(
    conversationId: string,
    messageId: string,
  ): Promise<ApiResponse<void>> {
    return this.request(
      "DELETE",
      `/conversations/${conversationId}/messages/${messageId}`,
    );
  }

  // SSE Streaming chat method (primary)
  async streamChatSSE(
    request: ChatRequest,
    callbacks: StreamingCallbacks,
  ): Promise<{ eventSource: EventSource; conversationId: string }> {
    const endpoint = `${this.baseURL.replace("/api", "")}/api/chat/stream`;
    const apiKey = this.client.defaults.headers.common["X-API-Key"] as string;

    // Create EventSource with POST data via URL params (EventSource limitation workaround)
    const params = new URLSearchParams({
      message: request.message,
      ...(request.conversation_id && {
        conversation_id: request.conversation_id,
      }),
      ...(request.agent_override && { agent_override: request.agent_override }),
      ...(request.context && { context: JSON.stringify(request.context) }),
      api_key: apiKey,
    });

    const eventSource = new EventSource(`${endpoint}?${params}`);
    let conversationId = request.conversation_id || "";

    eventSource.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        if (!isSSEEvent(parsed)) return;
        const sseEvent = parsed;
        switch (sseEvent.event) {
          case "stream_start":
            conversationId = sseEvent.data.conversation_id;
            break;
          case "token":
            callbacks.onToken?.(sseEvent.data.content, sseEvent.data.delta);
            break;
          case "function_call":
            callbacks.onFunctionCall?.(
              sseEvent.data.function_name,
              sseEvent.data.arguments,
            );
            break;
          case "tool_result":
            callbacks.onToolResult?.(
              sseEvent.data.tool_name,
              sseEvent.data.result,
            );
            break;
          case "agent_task_start":
            callbacks.onAgentTaskStart?.(
              sseEvent.data.task_id,
              sseEvent.data.agent_type,
              sseEvent.data.description,
            );
            break;
          case "agent_task_progress":
            callbacks.onAgentTaskProgress?.(
              sseEvent.data.task_id,
              sseEvent.data.progress,
              sseEvent.data.status,
            );
            break;
          case "agent_task_complete":
            callbacks.onAgentTaskComplete?.(
              sseEvent.data.task_id,
              sseEvent.data.result,
              sseEvent.data.success,
            );
            break;
          case "metrics":
            callbacks.onMetrics?.(sseEvent.data);
            break;
          case "error":
            callbacks.onError?.(
              sseEvent.data.error,
              sseEvent.data.code,
              sseEvent.data.recoverable ?? false,
            );
            break;
          case "done":
            callbacks.onDone?.(sseEvent.data.final_response, sseEvent.data);
            eventSource.close();
            break;
        }
      } catch (error) {
        logError(error as Error, {
          context: "sse_parse_error",
          rawData: event.data,
        });
      }
    };

    eventSource.onerror = (error) => {
      logError(new Error("SSE connection error"), {
        context: "sse_connection_error",
        error,
      });
      callbacks.onError?.("SSE connection failed", "SSE_ERROR", true);
    };

    return { eventSource, conversationId };
  }

  // WebSocket streaming chat method (fallback)
  async streamChatWebSocket(
    request: ChatRequest,
    callbacks: StreamingCallbacks,
  ): Promise<{ websocket: WebSocket; conversationId: string }> {
    const wsUrl =
      this.baseURL.replace("http", "ws").replace("/api", "") + "/ws/chat";
    const websocket = new WebSocket(wsUrl);
    let conversationId = request.conversation_id || "";

    return new Promise((resolve, reject) => {
      websocket.onopen = () => {
        // Authenticate
        const authMessage: WebSocketMessage = {
          type: "auth",
          api_key: this.client.defaults.headers.common["X-API-Key"] as string,
        };
        websocket.send(JSON.stringify(authMessage));

        // Send chat message
        const chatMessage: WebSocketMessage = {
          type: "chat",
          message: request.message,
          context: request.context,
          conversation_id: request.conversation_id,
        };
        websocket.send(JSON.stringify(chatMessage));

        resolve({ websocket, conversationId });
      };

      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.error) {
            callbacks.onError?.(data.error, "WS_ERROR", false);
            return;
          }

          // Handle current backend format (single response)
          if (data.response && data.done) {
            conversationId = data.conversation_id;
            callbacks.onDone?.(data.response, {
              conversation_id: data.conversation_id,
              agent_type: data.agent_type,
              processing_time: data.processing_time,
            });
          }
        } catch (error) {
          logError(error as Error, {
            context: "websocket_parse_error",
            rawData: event.data,
          });
        }
      };

      websocket.onerror = (error) => {
        logError(new Error("WebSocket connection error"), {
          context: "websocket_connection_error",
          error,
        });
        callbacks.onError?.("WebSocket connection failed", "WS_ERROR", false);
        reject(error);
      };

      websocket.onclose = () => {
        // Connection closed
      };
    });
  }

  // Unified streaming method with SSE primary, WebSocket fallback
  async streamChat(
    request: ChatRequest,
    callbacks: StreamingCallbacks,
  ): Promise<{ close: () => void; conversationId: string }> {
    try {
      // Try SSE first
      const { eventSource, conversationId } = await this.streamChatSSE(
        request,
        callbacks,
      );

      return {
        close: () => eventSource.close(),
        conversationId,
      };
    } catch (sseError) {
      logError(sseError as Error, {
        context: "sse_fallback_to_websocket",
      });

      // Fallback to WebSocket
      try {
        const { websocket, conversationId } = await this.streamChatWebSocket(
          request,
          callbacks,
        );

        return {
          close: () => websocket.close(),
          conversationId,
        };
      } catch (wsError) {
        logError(wsError as Error, {
          context: "websocket_fallback_failed",
        });
        throw new Error("Both SSE and WebSocket streaming failed");
      }
    }
  }

  // Legacy streaming method for backward compatibility
  async *streamChatLegacy(
    conversationId: string,
    message: ChatRequest,
  ): AsyncGenerator<StreamingChunk, void, unknown> {
    let finalContent = "";
    let isDone = false;

    const { close } = await this.streamChat(message, {
      onToken: (content, delta) => {
        finalContent += delta || content;
      },
      onDone: (finalResponse) => {
        finalContent = finalResponse;
        isDone = true;
      },
      onError: () => {
        isDone = true;
      },
    });

    // Simulate async generator behavior
    while (!isDone) {
      await new Promise((resolve) => setTimeout(resolve, 100));
      if (finalContent) {
        yield createStreamingChunk(finalContent, isDone);
      }
    }

    close();
  }

  // Agent methods
  async getAgents(): Promise<ApiResponse<Agent[]>> {
    const response = await this.request<Agent[]>("GET", "/agents");
    if (Array.isArray(response.data)) {
      response.data.forEach((agent, index) => {
        try {
          AgentSchema.parse(agent);
        } catch (error) {
          logError(error as Error, {
            context: "agent_validation",
            agentIndex: index,
          });
        }
      });
    }
    return response;
  }

  async getAgent(id: string): Promise<ApiResponse<Agent>> {
    const response = await this.request<Agent>("GET", `/agents/${id}`);
    try {
      AgentSchema.parse(response.data);
    } catch (error) {
      throw new ValidationError("Invalid agent data received");
    }
    return response;
  }

  async createAgent(
    agentData: Omit<Agent, "id" | "createdAt" | "updatedAt" | "metrics">,
  ): Promise<ApiResponse<Agent>> {
    return this.request("POST", "/agents", agentData);
  }

  async updateAgent(
    id: string,
    updates: Partial<Agent>,
  ): Promise<ApiResponse<Agent>> {
    return this.request("PUT", `/agents/${id}`, updates);
  }

  async deleteAgent(id: string): Promise<ApiResponse<void>> {
    return this.request("DELETE", `/agents/${id}`);
  }

  // Workspace methods
  async getWorkspaces(): Promise<ApiResponse<Workspace[]>> {
    return this.request("GET", "/workspaces");
  }

  async getWorkspace(id: string): Promise<ApiResponse<Workspace>> {
    return this.request("GET", `/workspaces/${id}`);
  }

  async createWorkspace(
    data: Omit<Workspace, "id" | "createdAt" | "updatedAt">,
  ): Promise<ApiResponse<Workspace>> {
    return this.request("POST", "/workspaces", data);
  }

  async updateWorkspace(
    id: string,
    updates: Partial<Workspace>,
  ): Promise<ApiResponse<Workspace>> {
    return this.request("PUT", `/workspaces/${id}`, updates);
  }

  async deleteWorkspace(id: string): Promise<ApiResponse<void>> {
    return this.request("DELETE", `/workspaces/${id}`);
  }

  // Plugin methods
  async getPlugins(): Promise<ApiResponse<Plugin[]>> {
    return this.request("GET", "/plugins");
  }

  async installPlugin(pluginId: string): Promise<ApiResponse<Plugin>> {
    return this.request("POST", `/plugins/${pluginId}/install`);
  }

  async uninstallPlugin(pluginId: string): Promise<ApiResponse<void>> {
    return this.request("DELETE", `/plugins/${pluginId}`);
  }

  async updatePluginSettings(
    pluginId: string,
    settings: Record<string, unknown>,
  ): Promise<ApiResponse<Plugin>> {
    return this.request("PUT", `/plugins/${pluginId}/settings`, { settings });
  }

  // Notifications methods
  async getNotifications(): Promise<ApiResponse<Notification[]>> {
    return this.request("GET", "/notifications");
  }

  async markNotificationAsRead(id: string): Promise<ApiResponse<void>> {
    return this.request("PUT", `/notifications/${id}/read`);
  }

  async deleteNotification(id: string): Promise<ApiResponse<void>> {
    return this.request("DELETE", `/notifications/${id}`);
  }

  // Health and Metrics methods
  async getHealthStatus(): Promise<ApiResponse<HealthStatus>> {
    const response = await this.request<HealthStatus>("GET", "/health");
    // Normalize to ApiResponse shape if backend omitted success
    if (response && typeof (response as any).success === "undefined") {
      return { success: true, data: response as unknown as HealthStatus };
    }
    return response;
  }

  async getMetrics(): Promise<ApiResponse<MetricsData>> {
    return this.request("GET", "/metrics");
  }

  // File upload methods
  async uploadFile(
    file: File,
    conversationId?: string,
    onProgress?: (progress: number) => void,
  ): Promise<ApiResponse<FileUploadResult>> {
    const formData = new FormData();
    formData.append("file", file);
    if (conversationId) {
      formData.append("conversationId", conversationId);
    }

    const config: AxiosRequestConfig = {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    };

    if (onProgress) {
      config.onUploadProgress = (progressEvent) => {
        if (progressEvent.total) {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total,
          );
          onProgress(progress);
        }
      };
    }

    return this.request("POST", "/upload", formData, config);
  }

  async uploadMultipleFiles(
    files: File[],
    conversationId?: string,
    onProgress?: (progress: number) => void,
  ): Promise<ApiResponse<Array<{ url: string; metadata: unknown }>>> {
    const formData = new FormData();
    files.forEach((file, index) => {
      formData.append(`files[${index}]`, file);
    });
    if (conversationId) {
      formData.append("conversationId", conversationId);
    }

    const config: AxiosRequestConfig = {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    };

    if (onProgress) {
      config.onUploadProgress = (progressEvent) => {
        if (progressEvent.total) {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total,
          );
          onProgress(progress);
        }
      };
    }

    return this.request("POST", "/upload/multiple", formData, config);
  }

  // Voice methods
  async transcribeAudio(
    audioFile: File,
  ): Promise<ApiResponse<{ text: string; confidence: number }>> {
    const formData = new FormData();
    formData.append("audio", audioFile);

    return this.request("POST", "/voice/transcribe", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  }

  async generateSpeech(
    text: string,
    voiceSettings?: VoiceSettings,
  ): Promise<ApiResponse<{ audioUrl: string }>> {
    return this.request("POST", "/voice/speak", { text, voiceSettings });
  }

  // Search methods
  async search(params: {
    q: string;
    types?: string[];
    dateRange?: string;
    sortBy?: string;
    limit?: number;
    offset?: number;
  }): Promise<unknown> {
    const response = await this.client.get("/api/search", { params });
    return response.data;
  }

  async searchGlobal(query: string, filters?: SearchFilters): Promise<unknown> {
    const params = { q: query, ...filters };
    return this.search(params);
  }

  // Settings methods
  async getSettings(): Promise<unknown> {
    const response = await this.client.get("/api/settings");
    return response.data;
  }

  async updateSettings(settings: Partial<unknown>): Promise<unknown> {
    const response = await this.client.put("/api/settings", settings);
    return response.data;
  }

  // File methods
  async deleteFile(fileId: string): Promise<void> {
    await this.client.delete(`/api/files/${fileId}`);
  }

  async getFiles(params?: {
    limit?: number;
    offset?: number;
  }): Promise<unknown> {
    const response = await this.client.get("/api/files", { params });
    return response.data;
  }

  // Generic HTTP methods for compatibility
  async post(
    endpoint: string,
    data?: unknown,
    config?: AxiosRequestConfig,
  ): Promise<unknown> {
    const response = await this.client.post(endpoint, data, config);
    return response.data;
  }

  async put(
    endpoint: string,
    data?: unknown,
    config?: AxiosRequestConfig,
  ): Promise<unknown> {
    const response = await this.client.put(endpoint, data, config);
    return response.data;
  }

  async patch(
    endpoint: string,
    data?: unknown,
    config?: AxiosRequestConfig,
  ): Promise<unknown> {
    const response = await this.client.patch(endpoint, data, config);
    return response.data;
  }
}

// Export singleton instance
export const apiClient = CartritaApiClient.createInstance();

// Export types
export type {
  ApiResponse,
  User,
  Conversation,
  Message,
  Agent,
  ChatRequest,
  ChatResponse,
};
