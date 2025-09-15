// Cartrita AI OS - State Management
// Comprehensive Jotai atoms for application state

import { atom } from "jotai";
import { atomWithStorage } from "jotai/utils";
import { atomFamily } from "jotai/utils";
import type {
  User,
  Conversation,
  Message,
  Agent,
  Workspace,
  Plugin,
  Notification,
  ThemeConfig,
  VoiceSettings,
  SearchFilters,
  ChatRequest,
} from "@/types";

// Core user state
export const userAtom = atomWithStorage<User | null>("user", null);
export const isAuthenticatedAtom = atom((get) => get(userAtom) !== null);
export const userPreferencesAtom = atom(
  (get) =>
    get(userAtom)?.preferences || {
      theme: "system" as const,
      language: "en",
      notifications: true,
      autoSave: true,
    },
);

// Authentication state
export const authTokenAtom = atomWithStorage<string | null>("authToken", null);
export const isLoadingAuthAtom = atom(false);
export const authErrorAtom = atom<string | null>(null);

// Conversations state
export const conversationsAtom = atomWithStorage<Conversation[]>(
  "conversations",
  [],
);
export const currentConversationIdAtom = atomWithStorage<string | null>(
  "currentConversationId",
  null,
);
export const conversationsLoadingAtom = atom(false);
export const conversationsErrorAtom = atom<string | null>(null);

// Current conversation state
export const currentConversationAtom = atom((get) => {
  const conversations = get(conversationsAtom);
  const currentId = get(currentConversationIdAtom);
  return conversations.find((conv) => conv.id === currentId) || null;
});

// Messages state
export const messagesAtom = atomFamily((conversationId: string) =>
  atomWithStorage<Message[]>(`messages_${conversationId}`, []),
);
export const messagesLoadingAtom = atomFamily((conversationId: string) =>
  atom(false),
);
export const messagesErrorAtom = atomFamily((conversationId: string) =>
  atom<string | null>(null),
);

// Current conversation messages
export const currentMessagesAtom = atom((get) => {
  const currentConversation = get(currentConversationAtom);
  if (!currentConversation) return [];
  return get(messagesAtom(currentConversation.id));
});

// Streaming state
export const streamingMessageAtom = atom<Message | null>(null);
export const isStreamingAtom = atom(
  (get) => get(streamingMessageAtom) !== null,
);
export const streamingConversationIdAtom = atom<string | null>(null);

// Agents state
export const agentsAtom = atomWithStorage<Agent[]>("agents", []);
export const selectedAgentIdAtom = atomWithStorage<string | null>(
  "selectedAgentId",
  null,
);
export const agentsLoadingAtom = atom(false);
export const agentsErrorAtom = atom<string | null>(null);

// Selected agent
export const selectedAgentAtom = atom((get) => {
  const agents = get(agentsAtom);
  const selectedId = get(selectedAgentIdAtom);
  return agents.find((agent) => agent.id === selectedId) || null;
});

// Workspaces state
export const workspacesAtom = atomWithStorage<Workspace[]>("workspaces", []);
export const currentWorkspaceIdAtom = atomWithStorage<string | null>(
  "currentWorkspaceId",
  null,
);
export const workspacesLoadingAtom = atom(false);
export const workspacesErrorAtom = atom<string | null>(null);

// Plugins state
export const pluginsAtom = atomWithStorage<Plugin[]>("plugins", []);
export const pluginsLoadingAtom = atom(false);
export const pluginsErrorAtom = atom<string | null>(null);

// Notifications state
export const notificationsAtom = atomWithStorage<Notification[]>(
  "notifications",
  [],
);
export const unreadNotificationsCountAtom = atom((get) => {
  const notifications = get(notificationsAtom);
  return notifications.filter((n) => !n.read).length;
});
export const notificationsLoadingAtom = atom(false);

// UI state
export const sidebarOpenAtom = atomWithStorage("sidebarOpen", true);
export const themeAtom = atomWithStorage<"light" | "dark" | "system">(
  "theme",
  "system",
);
export const languageAtom = atomWithStorage("language", "en");

// Chat input state
export const chatInputAtom = atom("");
export const chatInputFocusedAtom = atom(false);
export const chatInputHeightAtom = atom(0);

// Search state
export const searchQueryAtom = atom("");
export const searchFiltersAtom = atom<SearchFilters>({
  types: ["all"],
  dateRange: "all",
  sortBy: "relevance",
});
export const searchResultsAtom = atom<unknown[]>([]);
export const searchLoadingAtom = atom(false);
export const searchErrorAtom = atom<string | null>(null);

// File upload state
export const uploadedFilesAtom = atom<File[]>([]);
export const uploadProgressAtom = atom<Record<string, number>>({});
export const uploadErrorsAtom = atom<Record<string, string>>({});

// Voice state
export const isRecordingAtom = atom(false);
export const voiceSettingsAtom = atomWithStorage<VoiceSettings>(
  "voiceSettings",
  {
    enabled: true,
    language: "en",
    voice: "alloy",
    speed: 1.0,
    pitch: 1.0,
    volume: 1.0,
  },
);
export const transcriptionAtom = atom<string | null>(null);
export const transcriptionLoadingAtom = atom(false);

// Modal and overlay state
export const modalStackAtom = atom<
  Array<{
    id: string;
    type: string;
    props?: Record<string, unknown>;
  }>
>([]);
export const activeModalAtom = atom((get) => {
  const stack = get(modalStackAtom);
  return stack[stack.length - 1] || null;
});

// Loading states
export const globalLoadingAtom = atom(false);
export const loadingStatesAtom = atom<Record<string, boolean>>({});

// Error states
export const globalErrorAtom = atom<string | null>(null);
export const errorStatesAtom = atom<Record<string, string | null>>({});

// Network state
export const isOnlineAtom = atom(true);
export const networkErrorAtom = atom<string | null>(null);

// Keyboard shortcuts
export const keyboardShortcutsAtom = atomWithStorage("keyboardShortcuts", {
  newChat: "Ctrl+N",
  focusInput: "Ctrl+L",
  clearChat: "Ctrl+Shift+C",
  toggleSidebar: "Ctrl+B",
  search: "Ctrl+K",
  voiceInput: "Ctrl+M",
});

// Performance metrics
export const performanceMetricsAtom = atom({
  apiResponseTime: 0,
  renderTime: 0,
  memoryUsage: 0,
  networkRequests: 0,
});

// Cache state
export const cacheAtom = atom<Map<string, unknown>>(new Map());
export const cacheTimestampsAtom = atom<Map<string, number>>(new Map());

// Derived atoms for computed state
export const hasActiveConversationAtom = atom((get) => {
  const currentConversation = get(currentConversationAtom);
  return currentConversation !== null;
});

export const canSendMessageAtom = atom((get) => {
  const input = get(chatInputAtom).trim();
  const isStreaming = get(isStreamingAtom);
  const isAuthenticated = get(isAuthenticatedAtom);
  const hasAgent = get(selectedAgentAtom) !== null;

  return input.length > 0 && !isStreaming && isAuthenticated && hasAgent;
});

export const conversationStatsAtom = atom((get) => {
  const conversations = get(conversationsAtom);
  const messages = get(currentMessagesAtom);

  return {
    totalConversations: conversations.length,
    activeConversations: conversations.filter((c) => !c.isArchived).length,
    pinnedConversations: conversations.filter((c) => c.isPinned).length,
    archivedConversations: conversations.filter((c) => c.isArchived).length,
    totalMessages: messages.length,
    userMessages: messages.filter((m) => m.role === "user").length,
    assistantMessages: messages.filter((m) => m.role === "assistant").length,
  };
});

export const agentStatsAtom = atom((get) => {
  const agents = get(agentsAtom);

  return {
    totalAgents: agents.length,
    activeAgents: agents.filter(
      (a) => a.status !== "offline" && a.status !== "error",
    ).length,
    totalRequests: agents.reduce(
      (sum, a) =>
        sum +
        (typeof a.metadata?.totalRequests === "number"
          ? a.metadata.totalRequests
          : 0),
      0,
    ),
    averageSuccessRate:
      agents.length > 0
        ? agents.reduce(
            (sum, a) =>
              sum +
              (typeof a.metadata?.successRate === "number"
                ? a.metadata.successRate
                : 0),
            0,
          ) / agents.length
        : 0,
  };
});

// Optimistic updates
export const optimisticUpdatesAtom = atom<Map<string, unknown>>(new Map());

// Pending operations
export const pendingOperationsAtom = atom(new Set<string>());

// Retry state
export const retryStateAtom = atom<
  Record<
    string,
    {
      count: number;
      lastAttempt: number;
      nextRetry: number;
    }
  >
>({});

// Feature flags
export const featureFlagsAtom = atomWithStorage("featureFlags", {
  streaming: true,
  voiceInput: true,
  fileUpload: true,
  plugins: true,
  workspaces: true,
  notifications: true,
  search: true,
  themes: true,
  keyboardShortcuts: true,
  performanceMetrics: false,
});

// Settings state
export const settingsAtom = atomWithStorage("settings", {
  autoSave: true,
  showTimestamps: true,
  messageDensity: "comfortable" as "compact" | "comfortable" | "spacious",
  codeHighlighting: true,
  markdownRendering: true,
  autoScroll: true,
  reducedMotion: false,
  fontSize: "md" as "sm" | "md" | "lg",
  soundEffects: false,
  typingIndicator: true,
  readReceipts: false,
  messagePreview: true,
  conversationPreview: true,
});

// Export all atoms for use in components
export const atoms = {
  // User
  userAtom,
  isAuthenticatedAtom,
  userPreferencesAtom,

  // Auth
  authTokenAtom,
  isLoadingAuthAtom,
  authErrorAtom,

  // Conversations
  conversationsAtom,
  currentConversationIdAtom,
  currentConversationAtom,
  conversationsLoadingAtom,
  conversationsErrorAtom,

  // Messages
  messagesAtom,
  currentMessagesAtom,
  messagesLoadingAtom,
  messagesErrorAtom,

  // Streaming
  streamingMessageAtom,
  isStreamingAtom,
  streamingConversationIdAtom,

  // Agents
  agentsAtom,
  selectedAgentIdAtom,
  selectedAgentAtom,
  agentsLoadingAtom,
  agentsErrorAtom,

  // Workspaces
  workspacesAtom,
  currentWorkspaceIdAtom,
  workspacesLoadingAtom,
  workspacesErrorAtom,

  // Plugins
  pluginsAtom,
  pluginsLoadingAtom,

  // Notifications
  notificationsAtom,
  unreadNotificationsCountAtom,
  notificationsLoadingAtom,

  // UI
  sidebarOpenAtom,
  themeAtom,
  languageAtom,

  // Chat
  chatInputAtom,
  chatInputFocusedAtom,
  chatInputHeightAtom,

  // Search
  searchQueryAtom,
  searchFiltersAtom,
  searchResultsAtom,
  searchLoadingAtom,
  searchErrorAtom,

  // Files
  uploadedFilesAtom,
  uploadProgressAtom,
  uploadErrorsAtom,

  // Voice
  isRecordingAtom,
  voiceSettingsAtom,
  transcriptionAtom,
  transcriptionLoadingAtom,

  // Modals
  modalStackAtom,
  activeModalAtom,

  // Loading
  globalLoadingAtom,
  loadingStatesAtom,

  // Errors
  globalErrorAtom,
  errorStatesAtom,

  // Network
  isOnlineAtom,
  networkErrorAtom,

  // Shortcuts
  keyboardShortcutsAtom,

  // Performance
  performanceMetricsAtom,

  // Cache
  cacheAtom,
  cacheTimestampsAtom,

  // Computed
  hasActiveConversationAtom,
  canSendMessageAtom,
  conversationStatsAtom,
  agentStatsAtom,

  // Optimistic
  optimisticUpdatesAtom,

  // Pending
  pendingOperationsAtom,

  // Retry
  retryStateAtom,

  // Features
  featureFlagsAtom,

  // Settings
  settingsAtom,
};
