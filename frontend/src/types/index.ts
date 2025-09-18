/**
 * Core TypeScript types for Cartrita AI OS v2
 * Based on comprehensive UI/UX design specifications
 */

// ============================================================================
// User & Authentication Types
// ============================================================================

export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  preferences: UserPreferences;
  createdAt: string;
  lastActiveAt: string;
}

export interface UserPreferences {
  theme: 'dark' | 'light' | 'system';
  language: string;
  timezone: string;
  fontSize: 'sm' | 'md' | 'lg';
  sidebarCollapsed: boolean;
  rightSidebarVisible: boolean;
}

// ============================================================================
// Message & Conversation Types
// ============================================================================

export type MessageRole = 'user' | 'assistant' | 'system' | 'agent';

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  conversationId: string;
  parentId?: string;
  attachments?: Attachment[];
  metadata?: MessageMetadata;
  isStreaming?: boolean;
  isEdited?: boolean;
  tokens?: number;
}

export interface MessageMetadata {
  model?: string;
  temperature?: number;
  maxTokens?: number;
  agentId?: string;
  toolCalls?: ToolCall[];
  processingTime?: number;
  cost?: number;
}

export interface Attachment {
  id: string;
  name: string;
  type: 'file' | 'image' | 'audio' | 'video' | 'code' | 'document';
  url: string;
  size: number;
  mimeType: string;
  uploadedAt: string;
  metadata?: Record<string, unknown>;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  participants: Participant[];
  context: ConversationContext;
  settings: ConversationSettings;
  createdAt: string;
  updatedAt: string;
  isArchived: boolean;
  tags: string[];
}

export interface Participant {
  id: string;
  type: 'user' | 'agent';
  name: string;
  role?: string;
  avatar?: string;
  isActive: boolean;
}

export interface ConversationContext {
  files: ContextFile[];
  variables: Record<string, unknown>;
  memory: ConversationMemory[];
  scope: 'private' | 'shared' | 'public';
}

export interface ContextFile {
  id: string;
  name: string;
  path: string;
  type: string;
  content: string;
  lastModified: string;
}

export interface ConversationMemory {
  key: string;
  value: unknown;
  type: 'fact' | 'preference' | 'context' | 'instruction';
  timestamp: string;
  relevanceScore: number;
}

export interface ConversationSettings {
  model: string;
  temperature: number;
  maxTokens: number;
  systemPrompt?: string;
  autoSave: boolean;
  streamingEnabled: boolean;
  agentOrchestrationEnabled: boolean;
}

// ============================================================================
// Agent System Types
// ============================================================================

export interface Agent {
  id: string;
  name: string;
  description: string;
  avatar?: string;
  category: AgentCategory;
  capabilities: AgentCapability[];
  status: AgentStatus;
  version: string;
  config: AgentConfig;
  metadata: AgentMetadata;
  isCustom: boolean;
  createdAt: string;
  updatedAt: string;
}

export type AgentCategory =
  | 'coding'
  | 'research'
  | 'writing'
  | 'analysis'
  | 'creativity'
  | 'productivity'
  | 'communication'
  | 'custom';

export type AgentStatus = 'available' | 'busy' | 'offline' | 'maintenance';

export interface AgentCapability {
  id: string;
  name: string;
  description: string;
  type: 'tool' | 'skill' | 'knowledge' | 'integration';
  isRequired: boolean;
}

export interface AgentConfig {
  model: string;
  temperature: number;
  maxTokens: number;
  systemPrompt: string;
  tools: string[];
  permissions: AgentPermission[];
}

export interface AgentPermission {
  resource: string;
  actions: string[];
  scope: 'read' | 'write' | 'execute' | 'admin';
}

export interface AgentMetadata {
  author: string;
  license: string;
  documentation?: string;
  repository?: string;
  performance: AgentPerformance;
  usage: AgentUsage;
}

export interface AgentPerformance {
  averageResponseTime: number;
  successRate: number;
  errorRate: number;
  tokenEfficiency: number;
}

export interface AgentUsage {
  totalCalls: number;
  totalTokens: number;
  lastUsed: string;
  popularityScore: number;
}

export interface AgentState {
  id: string;
  agentId: string;
  status: 'idle' | 'processing' | 'waiting' | 'error';
  currentTask?: AgentTask;
  progress: number;
  messages: string[];
  startedAt: string;
  lastActivity: string;
}

export interface AgentTask {
  id: string;
  description: string;
  type: 'generation' | 'analysis' | 'tool_call' | 'research';
  input: unknown;
  expectedOutput: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  estimatedDuration: number;
}

// ============================================================================
// Tool System Types
// ============================================================================

export interface Tool {
  id: string;
  name: string;
  description: string;
  category: ToolCategory;
  parameters: ToolParameter[];
  returnType: string;
  version: string;
  isEnabled: boolean;
}

export type ToolCategory =
  | 'web_search'
  | 'file_operations'
  | 'code_execution'
  | 'api_calls'
  | 'data_analysis'
  | 'image_generation'
  | 'voice_synthesis'
  | 'custom';

export interface ToolParameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'array' | 'object';
  description: string;
  required: boolean;
  default?: unknown;
  validation?: ParameterValidation;
}

export interface ParameterValidation {
  min?: number;
  max?: number;
  pattern?: string;
  enum?: unknown[];
}

export interface ToolCall {
  id: string;
  toolId: string;
  parameters: Record<string, unknown>;
  result?: ToolResult;
  status: 'pending' | 'running' | 'completed' | 'error';
  startedAt: string;
  completedAt?: string;
}

export interface ToolResult {
  data: unknown;
  type: 'text' | 'json' | 'file' | 'image' | 'error';
  metadata?: Record<string, unknown>;
}

// ============================================================================
// Workflow & Orchestration Types
// ============================================================================

export interface Workflow {
  id: string;
  name: string;
  description: string;
  steps: WorkflowStep[];
  trigger: WorkflowTrigger;
  status: WorkflowStatus;
  version: string;
  createdAt: string;
  updatedAt: string;
}

export type WorkflowStatus = 'draft' | 'active' | 'paused' | 'completed' | 'error';

export interface WorkflowStep {
  id: string;
  name: string;
  type: 'agent' | 'tool' | 'condition' | 'parallel' | 'sequential';
  agentId?: string;
  toolId?: string;
  config: Record<string, unknown>;
  dependencies: string[];
  timeout?: number;
}

export interface WorkflowTrigger {
  type: 'manual' | 'schedule' | 'webhook' | 'file_change' | 'message';
  config: Record<string, unknown>;
}

// ============================================================================
// UI Component Props Types
// ============================================================================

export interface MessageBubbleProps {
  message: Message;
  variant?: MessageRole;
  isStreaming?: boolean;
  showTimestamp?: boolean;
  showActions?: boolean;
  onEdit?: (messageId: string, content: string) => void;
  onDelete?: (messageId: string) => void;
  onReact?: (messageId: string, reaction: string) => void;
  className?: string;
}

export interface MessageInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (content: string, attachments?: Attachment[]) => void;
  placeholder?: string;
  disabled?: boolean;
  attachments?: Attachment[];
  onAttachmentAdd?: (files: FileList) => void;
  onAttachmentRemove?: (attachmentId: string) => void;
  maxTokens?: number;
  className?: string;
}

export interface AgentCardProps {
  agent: Agent;
  isSelected?: boolean;
  showCapabilities?: boolean;
  showMetrics?: boolean;
  onSelect?: (agentId: string) => void;
  onConfigure?: (agentId: string) => void;
  className?: string;
}

export interface AgentOrchestratorProps {
  agents: Agent[];
  selectedAgents: string[];
  activeWorkflow?: Workflow;
  onAgentSelect: (agentId: string) => void;
  onWorkflowCreate: (agents: string[]) => void;
  onWorkflowExecute: (workflowId: string) => void;
  className?: string;
}

export interface ResponsiveSidebarProps {
  side: 'left' | 'right';
  isOpen: boolean;
  onToggle: () => void;
  width?: number;
  collapsedWidth?: number;
  children: React.ReactNode;
  className?: string;
}

export interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  color?: 'primary' | 'secondary' | 'accent';
  className?: string;
}

export interface TokenCounterProps {
  content: string;
  maxTokens: number;
  className?: string;
}

// ============================================================================
// Animation Component Props
// ============================================================================

export interface FadeInUpProps {
  children: React.ReactNode;
  delay?: number;
  duration?: number;
  className?: string;
}

export interface SlideInProps {
  children: React.ReactNode;
  direction: 'left' | 'right' | 'up' | 'down';
  delay?: number;
  duration?: number;
  className?: string;
}

// ============================================================================
// API & Service Types
// ============================================================================

export interface ApiResponse<T = unknown> {
  data?: T;
  error?: ApiError;
  success: boolean;
  message?: string;
  metadata?: {
    page?: number;
    limit?: number;
    total?: number;
    hasMore?: boolean;
  };
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
  timestamp: string;
}

export interface StreamingResponse {
  type: 'start' | 'chunk' | 'done' | 'error';
  data?: string;
  messageId?: string;
  error?: ApiError;
}

export interface PaginatedRequest {
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  filters?: Record<string, unknown>;
}

export interface SearchRequest extends PaginatedRequest {
  query: string;
  scope?: 'conversations' | 'agents' | 'files' | 'all';
  dateRange?: {
    from: string;
    to: string;
  };
}

// ============================================================================
// State Management Types (Jotai)
// ============================================================================

export interface AppState {
  user: User | null;
  theme: 'dark' | 'light' | 'system';
  sidebarLeft: SidebarState;
  sidebarRight: SidebarState;
  activeConversationId: string | null;
  isLoading: boolean;
  error: string | null;
}

export interface SidebarState {
  isOpen: boolean;
  width: number;
  activeTab: string;
}

export interface ConversationState {
  conversations: Record<string, Conversation>;
  activeId: string | null;
  isStreaming: boolean;
  streamingMessageId: string | null;
}

export interface AgentOrchestrationState {
  availableAgents: Agent[];
  selectedAgents: string[];
  activeWorkflow: Workflow | null;
  agentStates: Record<string, AgentState>;
  isExecuting: boolean;
}

// ============================================================================
// Hook Return Types
// ============================================================================

export interface UseSSEChatReturn {
  messages: Message[];
  isConnected: boolean;
  error: string | null;
  sendMessage: (content: string, attachments?: Attachment[]) => void;
  disconnect: () => void;
}

export interface UseConversationsReturn {
  conversations: Conversation[];
  isLoading: boolean;
  error: string | null;
  createConversation: (title: string) => Promise<Conversation>;
  deleteConversation: (id: string) => Promise<void>;
  updateConversation: (id: string, updates: Partial<Conversation>) => Promise<void>;
}

// ============================================================================
// Event Types
// ============================================================================

export interface ConversationEvent {
  type: 'message_added' | 'message_updated' | 'conversation_updated' | 'participant_joined' | 'participant_left';
  conversationId: string;
  data: unknown;
  timestamp: string;
}

export interface AgentEvent {
  type: 'agent_started' | 'agent_completed' | 'agent_error' | 'tool_called' | 'workflow_updated';
  agentId: string;
  data: unknown;
  timestamp: string;
}

// ============================================================================
// Utility Types
// ============================================================================

export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export type RequireAtLeastOne<T, Keys extends keyof T = keyof T> =
  Pick<T, Exclude<keyof T, Keys>> & {
    [K in Keys]-?: Required<Pick<T, K>> & Partial<Pick<T, Exclude<Keys, K>>>;
  }[Keys];

export type Nullable<T> = T | null;
export type Optional<T> = T | undefined;

// ============================================================================
// Environment & Configuration Types
// ============================================================================

export interface AppConfig {
  apiUrl: string;
  wsUrl: string;
  maxTokens: number;
  maxFileSize: number;
  supportedFileTypes: string[];
  features: FeatureFlags;
}

export interface FeatureFlags {
  voiceInput: boolean;
  fileUpload: boolean;
  agentOrchestration: boolean;
  realTimeCollaboration: boolean;
  customAgents: boolean;
  advancedSearch: boolean;
}

// Export all types as a namespace for easier importing
// Note: tokens are defined inline in Tailwind config
