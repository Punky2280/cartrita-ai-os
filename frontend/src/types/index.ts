// Cartrita AI OS - TypeScript Type Definitions
// Comprehensive types for the enhanced ChatGPT-like frontend

export interface User {
  id: string
  email: string
  name: string
  avatar?: string
  bio?: string
  apiKeys?: {
    openai?: string
    google?: string
    huggingface?: string
  }
  preferences: UserPreferences
  createdAt: string
  updatedAt: string
  lastLoginAt?: string
  isActive: boolean
  role: 'user' | 'admin' | 'moderator'
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system'
  language: string
  notifications: NotificationSettings
  privacy: PrivacySettings
  accessibility: AccessibilitySettings
}

export interface NotificationSettings {
  email: boolean
  push: boolean
  sound: boolean
  desktop: boolean
}

export interface PrivacySettings {
  dataCollection?: boolean
  saveHistory?: boolean
  profileVisibility?: boolean
  showActivity?: boolean
}

export interface AccessibilitySettings {
  highContrast: boolean
  reducedMotion: boolean
  fontSize: 'small' | 'medium' | 'large'
  screenReader: boolean
}

export interface Conversation {
  id: string
  title: string
  userId: string
  messages: Message[]
  createdAt: string
  updatedAt: string
  isArchived: boolean
  isPinned: boolean
  tags: string[]
  metadata: ConversationMetadata
}

export interface ConversationMetadata {
  totalMessages: number
  lastActivity: string
  agentUsed: string
  tokensUsed: number
  processingTime: number
}

export interface Message {
  id: string
  conversationId: string
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  attachments?: Attachment[]
  metadata: Record<string, unknown>
  createdAt: string
  updatedAt: string
  isEdited: boolean
  tokens?: number
  processingTime?: number
  // Legacy fields for compatibility
  timestamp?: string
  reactions?: Reaction[]
}

export interface MessageMetadata {
  agent?: string
  model?: string
  tokens?: number
  processingTime?: number
  confidence?: number
  sources?: Source[]
  error?: string
  streaming?: boolean
  processing?: boolean
}

export interface Attachment {
  id: string
  type: 'image' | 'file' | 'code' | 'link'
  name: string
  url: string
  size?: number
  mimeType?: string
  metadata?: Record<string, unknown>
}

export interface Reaction {
  emoji: string
  count: number
  users: string[]
}

export interface Source {
  id: string
  title: string
  url?: string
  content: string
  relevanceScore: number
  metadata: Record<string, unknown>
}

export interface Agent {
  id: string
  name: string
  type: AgentType
  status: 'idle' | 'busy' | 'offline' | 'error'
  model: string
  description?: string
  capabilities?: string[]
  last_used_at?: string
  usage_count?: number
  metadata?: {
    version?: string
    uptime?: number
    memory_usage?: number
    queue_size?: number
    [key: string]: unknown
  }
  // Legacy fields for compatibility
  version?: string
}

export type AgentType =
  | 'supervisor'
  | 'research'
  | 'code'
  | 'computer_use'
  | 'knowledge'
  | 'task'

export interface AgentMetadata {
  lastActive: string
  totalRequests: number
  successRate: number
  averageResponseTime: number
  specialties: string[]
  limitations: string[]
}

export interface ChatRequest {
  message: string
  conversation_id?: string
  context?: Record<string, unknown>
  agent_override?: AgentType
  stream?: boolean
  temperature?: number
  max_tokens?: number
  tools?: string[]
  // Legacy fields for compatibility
  conversationId?: string
  userId?: string
  agentOverride?: string
  attachments?: Attachment[]
  metadata?: Record<string, unknown>
}

export interface ChatResponse {
  response: string
  conversation_id: string
  agent_type: AgentType
  message?: Message
  metadata?: Record<string, unknown>
  processing_time?: number
  token_usage?: {
    prompt_tokens?: number
    completion_tokens?: number
    total_tokens?: number
  }
  sources?: string[]
  // Legacy fields for compatibility
  conversationId?: string
  suggestions?: string[]
  followUpQuestions?: string[]
}

export interface ChatResponseMetadata {
  agent: string
  model: string
  tokensUsed: number
  processingTime: number
  confidence: number
  streaming: boolean
}

export interface StreamingChunk {
  content: string
  done: boolean
  metadata?: {
    tokens?: number
    agent?: string
    confidence?: number
    streaming?: boolean
  }
}

export interface HealthStatus {
  status: 'healthy' | 'unhealthy' | 'degraded'
  version: string
  timestamp: string
  services: Record<string, ServiceStatus>
  uptime: number
  responseTime: number
}

export interface ServiceStatus {
  status: 'healthy' | 'unhealthy' | 'degraded'
  responseTime?: number
  lastCheck: string
  details?: Record<string, unknown>
}

export interface MetricsData {
  requests: RequestMetrics
  performance: PerformanceMetrics
  agents: AgentMetrics
  system: SystemMetrics
}

export interface RequestMetrics {
  total: number
  successful: number
  failed: number
  averageResponseTime: number
  requestsPerMinute: number
}

export interface PerformanceMetrics {
  cpuUsage: number
  memoryUsage: number
  diskUsage: number
  networkUsage: number
}

export interface AgentMetrics {
  totalAgents: number
  activeAgents: number
  averageLoad: number
  errorRate: number
}

export interface SystemMetrics {
  uptime: number
  totalUsers: number
  activeConversations: number
  totalMessages: number
}

export type SearchResultType = 'all' | 'conversation' | 'message' | 'agent' | 'file'

export interface SearchResult {
  id: string
  title: string
  snippet?: string
  type: SearchResultType
  url?: string
  timestamp: string
  metadata?: {
    author?: string
    conversationTitle?: string
    agentName?: string
    fileSize?: number
    fileType?: string
  }
}

export interface SearchFilters {
  types: SearchResultType[]
  dateRange: 'all' | 'today' | 'week' | 'month' | 'year'
  sortBy: 'relevance' | 'date' | 'title'
}

export interface SearchResponse {
  results: SearchResult[]
  total: number
  hasMore: boolean
  query: string
}

export interface Plugin {
  id: string
  name: string
  description: string
  version: string
  author: string
  enabled: boolean
  settings: Record<string, unknown>
  capabilities: string[]
}

export interface Workspace {
  id: string
  name: string
  description: string
  ownerId: string
  members: WorkspaceMember[]
  settings: WorkspaceSettings
  createdAt: string
  updatedAt: string
}

export interface WorkspaceMember {
  userId: string
  role: 'owner' | 'admin' | 'member'
  permissions: string[]
  joinedAt: string
}

export interface WorkspaceSettings {
  isPublic: boolean
  allowGuestAccess: boolean
  maxMembers: number
  features: string[]
}

export interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message: string
  timestamp: string
  read: boolean
  actionUrl?: string
  metadata?: Record<string, unknown>
}

export interface ThemeConfig {
  name: string
  colors: {
    primary: string
    secondary: string
    accent: string
    background: string
    foreground: string
    muted: string
    border: string
  }
  fonts: {
    sans: string
    mono: string
  }
}

export interface KeyboardShortcut {
  key: string
  ctrl?: boolean
  shift?: boolean
  alt?: boolean
  meta?: boolean
  description: string
  action: string
}

export interface VoiceSettings {
  enabled: boolean
  language: string
  voice: string
  speed: number
  pitch: number
  volume?: number
}

export interface CodeExecutionResult {
  success: boolean
  output: string
  error?: string
  executionTime: number
  language: string
}

export interface FileUploadResult {
  success: boolean
  fileId: string
  fileName: string
  fileSize: number
  mimeType: string
  url: string
}

export interface ExportOptions {
  format: 'json' | 'markdown' | 'pdf' | 'txt'
  includeMetadata: boolean
  includeAttachments: boolean
  dateRange?: {
    start: string
    end: string
  }
}

export interface ImportResult {
  success: boolean
  conversationsImported: number
  messagesImported: number
  errors: string[]
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  message?: string
  metadata?: Record<string, unknown>
}

export interface PaginatedResponse<T> {
  data: T[]
  pagination: {
    page: number
    limit: number
    total: number
    totalPages: number
    hasNext: boolean
    hasPrev: boolean
  }
}

// WebSocket Message Types
export interface WSMessage {
  type: 'chat' | 'status' | 'notification' | 'error'
  payload: unknown
  timestamp: string
  conversationId?: string
}

export interface WSChatMessage extends WSMessage {
  type: 'chat'
  payload: {
    message: Message
    streaming?: boolean
    done?: boolean
  }
}

export interface WSStatusMessage extends WSMessage {
  type: 'status'
  payload: {
    status: 'connected' | 'disconnected' | 'reconnecting'
    details?: unknown
  }
}

// Form Types
export interface LoginForm {
  email: string
  password: string
  rememberMe: boolean
}

export interface RegisterForm {
  name: string
  email: string
  password: string
  confirmPassword: string
  acceptTerms: boolean
}

export interface ProfileForm {
  name: string
  email: string
  avatar?: File
  preferences: UserPreferences
}

export interface ConversationForm {
  title: string
  description?: string
  tags: string[]
  isPublic: boolean
}

// Utility Types
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P]
}

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>

export type RequireAtLeastOne<T, Keys extends keyof T = keyof T> = Pick<T, Exclude<keyof T, Keys>> & {
  [K in Keys]-?: Required<Pick<T, K>> & Partial<Pick<T, Keys>>
}[Keys]

// Component Props Types
export interface BaseComponentProps {
  className?: string
  children?: React.ReactNode
  id?: string
  'data-testid'?: string
}

export interface LoadingProps extends BaseComponentProps {
  size?: 'sm' | 'md' | 'lg'
  variant?: 'spinner' | 'dots' | 'pulse'
  text?: string
}

export interface InputProps extends BaseComponentProps {
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url' | 'search'
  placeholder?: string
  value?: string
  defaultValue?: string
  disabled?: boolean
  required?: boolean
  error?: string
  onChange?: (event: React.ChangeEvent<HTMLInputElement>) => void
  onBlur?: (event: React.FocusEvent<HTMLInputElement>) => void
  onFocus?: (event: React.FocusEvent<HTMLInputElement>) => void
}

export interface TextareaProps extends InputProps {
  rows?: number
  resize?: 'none' | 'vertical' | 'horizontal' | 'both'
}

export interface ModalProps extends BaseComponentProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  description?: string
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full'
  closable?: boolean
  backdrop?: 'blur' | 'dark' | 'none'
}

export interface DropdownProps extends BaseComponentProps {
  trigger: React.ReactNode
  items: DropdownItem[]
  placement?: 'top' | 'bottom' | 'left' | 'right'
  align?: 'start' | 'center' | 'end'
  onSelect?: (item: DropdownItem) => void
}

export interface DropdownItem {
  id: string
  label: string
  icon?: React.ReactNode
  disabled?: boolean
  divider?: boolean
  children?: DropdownItem[]
}

// Hook Types
export interface UseChatOptions {
  conversationId?: string
  autoScroll?: boolean
  onMessage?: (message: Message) => void
  onError?: (error: Error) => void
  onComplete?: () => void
}

export interface UseStreamingOptions {
  onChunk?: (chunk: StreamingChunk) => void
  onComplete?: (message: Message) => void
  onError?: (error: Error) => void
}

export interface UseSearchOptions {
  debounceMs?: number
  minQueryLength?: number
  filters?: SearchFilters
  onResults?: (results: SearchResult) => void
}

// Context Types
export interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (credentials: LoginForm) => Promise<void>
  logout: () => Promise<void>
  register: (data: RegisterForm) => Promise<void>
  updateProfile: (data: ProfileForm) => Promise<void>
}

export interface ChatContextType {
  conversations: Conversation[]
  currentConversation: Conversation | null
  isLoading: boolean
  sendMessage: (message: string, options?: Partial<ChatRequest>) => Promise<void>
  createConversation: (title?: string) => Promise<Conversation>
  deleteConversation: (id: string) => Promise<void>
  switchConversation: (id: string) => void
  clearConversation: () => void
}

export interface ThemeContextType {
  theme: 'light' | 'dark' | 'system'
  setTheme: (theme: 'light' | 'dark' | 'system') => void
  resolvedTheme: 'light' | 'dark'
}

export interface NotificationContextType {
  notifications: Notification[]
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void
  removeNotification: (id: string) => void
  markAsRead: (id: string) => void
  clearAll: () => void
}

// Error Types
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public response?: unknown,
    public requestId?: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export class ValidationError extends Error {
  constructor(
    public field: string,
    message: string,
    public value?: unknown
  ) {
    super(message)
    this.name = 'ValidationError'
  }
}

export class NetworkError extends Error {
  constructor(
    message: string,
    public originalError?: Error
  ) {
    super(message)
    this.name = 'NetworkError'
  }
}

export class AuthenticationError extends Error {
  constructor(
    message: string,
    public redirectTo?: string
  ) {
    super(message)
    this.name = 'AuthenticationError'
  }
}

// Constants
export const AGENT_TYPES: Record<AgentType, { name: string; description: string; icon: string }> = {
  supervisor: {
    name: 'Supervisor',
    description: 'GPT-4.1 orchestrator for intelligent task delegation',
    icon: '🧠'
  },
  research: {
    name: 'Research Agent',
    description: 'GPT-5 powered web search and information gathering',
    icon: '🔍'
  },
  code: {
    name: 'Code Agent',
    description: 'GPT-5 powered code generation and analysis',
    icon: '💻'
  },
  computer_use: {
    name: 'Computer Use Agent',
    description: 'GPT-5 powered system interaction and automation',
    icon: '🖥️'
  },
  knowledge: {
    name: 'Knowledge Agent',
    description: 'GPT-5 powered document search and RAG',
    icon: '📚'
  },
  task: {
    name: 'Task Agent',
    description: 'GPT-5 powered task planning and project management',
    icon: '📋'
  }
}

export interface UserSettings {
  name: string
  email: string
  avatar?: string
  bio?: string
  theme: 'light' | 'dark' | 'system'
  apiKeys?: {
    openai?: string
    google?: string
    huggingface?: string
  }
  appearance?: {
    compactMode?: boolean
    showAnimations?: boolean
    highContrast?: boolean
  }
  notifications?: {
    email?: boolean
    push?: boolean
    messages?: boolean
    agentStatus?: boolean
    systemUpdates?: boolean
  }
  privacy?: {
    dataCollection?: boolean
    saveHistory?: boolean
    profileVisibility?: boolean
    showActivity?: boolean
  }
}

export type Theme = 'light' | 'dark' | 'system'

// WebSocket Message Types for Deepgram Integration
export interface WebSocketMessage {
  type: 'transcript' | 'analytics' | 'error' | 'state' | 'metrics' | 'connection' | 'audio'
  data: unknown
  timestamp: number
  messageId?: string
}

export interface TranscriptMessage extends WebSocketMessage {
  type: 'transcript'
  data: {
    text: string
    confidence: number
    is_final: boolean
    speaker?: number
    words?: Array<{
      word: string
      start: number
      end: number
      confidence: number
    }>
  }
}

export interface AnalyticsMessage extends WebSocketMessage {
  type: 'analytics'
  data: {
    sentiment: {
      score: number
      label: 'positive' | 'negative' | 'neutral'
      confidence: number
    }
    topics: Array<{
      name: string
      confidence: number
      keywords: string[]
    }>
    emotions: Array<{
      emotion: string
      confidence: number
    }>
    speaker_id?: string
    language_detected?: string
  }
}

export interface ErrorMessage extends WebSocketMessage {
  type: 'error'
  data: {
    code: string
    message: string
    details?: unknown
  }
}

export interface StateMessage extends WebSocketMessage {
  type: 'state'
  data: {
    state: 'idle' | 'recording' | 'processing' | 'speaking' | 'error'
    previousState?: string
  }
}

export interface ConnectionMessage extends WebSocketMessage {
  type: 'connection'
  data: {
    status: 'connected' | 'disconnected' | 'reconnecting' | 'failed'
    reason?: string
  }
}

export interface AudioMessage extends WebSocketMessage {
  type: 'audio'
  data: {
    format: string
    sampleRate: number
    channels: number
    duration?: number
  }
}

// Audio Analytics Types
export interface AudioAnalytics {
  id: string
  timestamp: string
  duration: number
  sampleRate: number
  channels: number
  format: string
  quality: number
  noiseLevel: number
  clarity: number
  transcription?: string
  confidence?: number
  language?: string
  speakerCount?: number
  sentiment?: 'positive' | 'negative' | 'neutral'
  keywords?: string[]
  topics?: string[]
}

export interface VoiceMetrics {
  signalQuality: number
  noiseLevel: number
  clarity: number
  volume: number
  pitch: number
  speakingRate: number
  pauses: number
  fillerWords: number
  confidence: number
  language: string
  accent?: string
  emotion?: string
}