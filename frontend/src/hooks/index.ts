// Cartrita AI OS - React Query Hooks
// Comprehensive data fetching and mutation hooks

import { useQuery, useMutation, useQueryClient, useInfiniteQuery } from '@tanstack/react-query'
import { useAtomValue, useSetAtom, useAtom } from 'jotai'
import { toast } from 'sonner'
import { apiClient } from '@/services/api'
import {
  userAtom,
  conversationsAtom,
  currentConversationIdAtom,
  messagesAtom,
  streamingMessageAtom,
  agentsAtom,
  workspacesAtom,
  pluginsAtom,
  notificationsAtom,
  searchResultsAtom,
  searchLoadingAtom,
  searchErrorAtom,
  authTokenAtom,
  isLoadingAuthAtom,
  authErrorAtom,
  conversationsLoadingAtom,
  conversationsErrorAtom,
  agentsLoadingAtom,
  agentsErrorAtom,
  workspacesLoadingAtom,
  workspacesErrorAtom,
  pluginsLoadingAtom,
  notificationsLoadingAtom,
  messagesLoadingAtom,
  messagesErrorAtom,
  settingsAtom
} from '@/stores'
import type {
  User,
  Conversation,
  Message,
  Agent,
  Workspace,
  Plugin,
  Notification,
  ChatRequest,
  SearchFilters,
  VoiceSettings,
  ThemeConfig
} from '@/types'

// Query Keys
export const queryKeys = {
  user: ['user'] as const,
  conversations: ['conversations'] as const,
  conversation: (id: string) => ['conversations', id] as const,
  messages: (conversationId: string) => ['conversations', conversationId, 'messages'] as const,
  agents: ['agents'] as const,
  agent: (id: string) => ['agents', id] as const,
  workspaces: ['workspaces'] as const,
  workspace: (id: string) => ['workspaces', id] as const,
  plugins: ['plugins'] as const,
  plugin: (id: string) => ['plugins', id] as const,
  notifications: ['notifications'] as const,
  search: (query: string, filters?: SearchFilters) => ['search', query, filters] as const,
  health: ['health'] as const,
  metrics: ['metrics'] as const
}

// Authentication Hooks
export function useAuth() {
  const setUser = useSetAtom(userAtom)
  const setAuthToken = useSetAtom(authTokenAtom)
  const setIsLoading = useSetAtom(isLoadingAuthAtom)

  const loginMutation = useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      apiClient.login(email, password),
    onMutate: () => {
      setIsLoading(true)
    },
    onSuccess: (response: any) => {
      if (response.success && response.data) {
        setUser(response.data.user)
        setAuthToken(response.data.token)
        apiClient.setAuthToken(response.data.token)
        toast.success('Login successful')
      }
    },
    onError: (error: any) => {
      toast.error(error.message || 'Login failed')
    },
    onSettled: () => {
      setIsLoading(false)
    }
  })

  const registerMutation = useMutation({
    mutationFn: ({ email, password, name }: { email: string; password: string; name: string }) =>
      apiClient.register({ email, password, name }),
    onMutate: () => {
      setIsLoading(true)
    },
    onSuccess: (response: any) => {
      if (response.success && response.data) {
        setUser(response.data.user)
        setAuthToken(response.data.token)
        apiClient.setAuthToken(response.data.token)
        toast.success('Registration successful')
      }
    },
    onError: (error: any) => {
      toast.error(error.message || 'Registration failed')
    },
    onSettled: () => {
      setIsLoading(false)
    }
  })

  const logoutMutation = useMutation({
    mutationFn: () => apiClient.logout(),
    onSuccess: () => {
      setUser(null)
      setAuthToken(null)
      apiClient.removeAuthToken()
      toast.success('Logged out successfully')
    },
    onError: (error: any) => {
      toast.error('Logout failed')
    }
  })

  return {
    login: loginMutation.mutate,
    register: registerMutation.mutate,
    logout: logoutMutation.mutate,
    isLoading: loginMutation.isPending || registerMutation.isPending || logoutMutation.isPending
  }
}

export function useUser() {
  const queryClient = useQueryClient()
  const setUser = useSetAtom(userAtom)

  const { data: user, ...query } = useQuery({
    queryKey: queryKeys.user,
    queryFn: () => apiClient.getCurrentUser(),
    enabled: false, // Only fetch when explicitly called
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1
  })

  const updatePreferencesMutation = useMutation({
    mutationFn: (preferences: Partial<User['preferences']>) =>
      apiClient.updateUserPreferences(preferences),
    onSuccess: (response: any) => {
      if (response.success && response.data) {
        setUser(response.data)
        queryClient.invalidateQueries({ queryKey: queryKeys.user })
        toast.success('Preferences updated')
      }
    },
    onError: (error: any) => {
      toast.error('Failed to update preferences')
    }
  })

  const updateThemeMutation = useMutation({
    mutationFn: (themeConfig: ThemeConfig) =>
      apiClient.updateThemeConfig(themeConfig),
    onSuccess: (response: any) => {
      if (response.success && response.data) {
        setUser(response.data)
        queryClient.invalidateQueries({ queryKey: queryKeys.user })
        toast.success('Theme updated')
      }
    },
    onError: (error: any) => {
      toast.error('Failed to update theme')
    }
  })

  const updateVoiceSettingsMutation = useMutation({
    mutationFn: (voiceSettings: VoiceSettings) =>
      apiClient.updateVoiceSettings(voiceSettings),
    onSuccess: (response: any) => {
      if (response.success && response.data) {
        setUser(response.data)
        queryClient.invalidateQueries({ queryKey: queryKeys.user })
        toast.success('Voice settings updated')
      }
    },
    onError: (error: any) => {
      toast.error('Failed to update voice settings')
    }
  })

  return {
    user: user?.data || null,
    ...query,
    updatePreferences: updatePreferencesMutation.mutate,
    updateTheme: updateThemeMutation.mutate,
    updateVoiceSettings: updateVoiceSettingsMutation.mutate,
    isUpdating: updatePreferencesMutation.isPending ||
                updateThemeMutation.isPending ||
                updateVoiceSettingsMutation.isPending
  }
}

// Conversations Hooks
export function useConversations(filters?: SearchFilters) {
  const setConversations = useSetAtom(conversationsAtom)
  const setLoading = useSetAtom(conversationsLoadingAtom)

  return useQuery({
    queryKey: [...queryKeys.conversations, filters],
    queryFn: () => apiClient.getConversations(filters),
    staleTime: 30 * 1000, // 30 seconds
    refetchOnWindowFocus: true
  })
}

export function useConversation(id: string) {
  const queryClient = useQueryClient()
  const setCurrentConversationId = useSetAtom(currentConversationIdAtom)

  return useQuery({
    queryKey: queryKeys.conversation(id),
    queryFn: () => apiClient.getConversation(id),
    enabled: !!id,
    staleTime: 60 * 1000, // 1 minute
    retry: 2
  })
}

export function useCreateConversation() {
  const queryClient = useQueryClient()
  const setConversations = useSetAtom(conversationsAtom)
  const setCurrentConversationId = useSetAtom(currentConversationIdAtom)

  return useMutation({
    mutationFn: (data: {
      title?: string
      agentId?: string
      workspaceId?: string
      initialMessage?: string
    }) => apiClient.createConversation(data),
    onSuccess: (response: any) => {
      if (response.success && response.data) {
        // Add to conversations list
        setConversations(prev => [response.data, ...prev])
        setCurrentConversationId(response.data.id)

        // Invalidate related queries
        queryClient.invalidateQueries({ queryKey: queryKeys.conversations })

        toast.success('Conversation created')
      }
    },
    onError: (error: any) => {
      toast.error('Failed to create conversation')
    }
  })
}

export function useUpdateConversation() {
  const queryClient = useQueryClient()
  const setConversations = useSetAtom(conversationsAtom)

  return useMutation({
    mutationFn: ({
      id,
      updates
    }: {
      id: string
      updates: Partial<Pick<Conversation, 'title' | 'isArchived' | 'tags'>>
    }) => apiClient.updateConversation(id, updates),
    onSuccess: (response: any, { id }) => {
      if (response.success && response.data) {
        // Update in conversations list
        setConversations(prev =>
          prev.map(conv => conv.id === id ? response.data : conv)
        )

        // Update in cache
        queryClient.setQueryData(queryKeys.conversation(id), { data: response.data })

        toast.success('Conversation updated')
      }
    },
    onError: (error: any) => {
      toast.error('Failed to update conversation')
    }
  })
}

export function useDeleteConversation() {
  const queryClient = useQueryClient()
  const setConversations = useSetAtom(conversationsAtom)
  const setCurrentConversationId = useSetAtom(currentConversationIdAtom)

  return useMutation({
    mutationFn: (id: string) => apiClient.deleteConversation(id),
    onSuccess: (_, id) => {
      // Remove from conversations list
      setConversations(prev => prev.filter(conv => conv.id !== id))

      // Clear current conversation if it was deleted
      setCurrentConversationId(prev => prev === id ? null : prev)

      // Remove from cache
      queryClient.removeQueries({ queryKey: queryKeys.conversation(id) })
      queryClient.removeQueries({ queryKey: queryKeys.messages(id) })

      toast.success('Conversation deleted')
    },
    onError: (error: any) => {
      toast.error('Failed to delete conversation')
    }
  })
}

// Messages Hooks
export function useMessages(conversationId: string, options?: {
  limit?: number
  offset?: number
  before?: string
  after?: string
}) {
  const setMessages = useSetAtom(messagesAtom(conversationId))
  const setLoading = useSetAtom(messagesLoadingAtom(conversationId))

  return useQuery({
    queryKey: [...queryKeys.messages(conversationId), options],
    queryFn: () => apiClient.getMessages(conversationId, options),
    enabled: !!conversationId,
    staleTime: 10 * 1000, // 10 seconds
    refetchOnWindowFocus: false
  })
}

export function useInfiniteMessages(conversationId: string, limit = 50) {
  const setMessages = useSetAtom(messagesAtom(conversationId))

  return useInfiniteQuery({
    queryKey: [...queryKeys.messages(conversationId), 'infinite'],
    queryFn: ({ pageParam = 0 }) =>
      apiClient.getMessages(conversationId, { limit, offset: pageParam }),
    initialPageParam: 0,
    enabled: !!conversationId,
    getNextPageParam: (lastPage: any, allPages) => {
      if (lastPage.data && lastPage.data.length === limit) {
        return allPages.length * limit
      }
      return undefined
    },
    select: (data) => {
      // Combine all pages into a single array
      const allMessages = data.pages.flatMap(page => page.data || [])
      setMessages(allMessages)
      return data
    },
    staleTime: 10 * 1000
  })
}

// Temporarily disabled due to Jotai atom type issues
// export function useSendMessage() {
//   const queryClient = useQueryClient()
//   const setStreamingMessage = useSetAtom(streamingMessageAtom)

//   return useMutation({
//     mutationFn: ({
//       conversationId,
//       message
//     }: {
//       conversationId: string
//       message: ChatRequest
//     }) => apiClient.sendMessage(conversationId, message),
//     onSuccess: (response: any, { conversationId }) => {
//       if (response.success && response.data) {
//         // Add the response message to the conversation
//         const newMessage: Message = {
//           id: response.data.id || `msg_${Date.now()}`,
//           conversationId,
//           role: 'assistant',
//           content: response.data.content,
//           timestamp: new Date().toISOString(),
//           metadata: response.data.metadata || {}
//         }

//         // Update messages cache
//         queryClient.setQueryData(
//           queryKeys.messages(conversationId),
//           (old: any) => ({
//             ...old,
//             data: [...(old?.data || []), newMessage]
//           })
//         )

//         // Clear streaming state
//         setStreamingMessage(null)

//         // Update conversation's last message timestamp
//         queryClient.invalidateQueries({
//           queryKey: queryKeys.conversation(conversationId)
//         })
//       }
//     },
//     onError: (error: any) => {
//       setStreamingMessage(null)
//       toast.error('Failed to send message')
//     }
//   })
// }

// Temporarily disabled due to Jotai atom type issues
// export function useStreamMessage() {
//   const setStreamingMessage = useSetAtom(streamingMessageAtom)

//   return useMutation({
//     mutationFn: async ({
//       conversationId,
//       message
//     }: {
//       conversationId: string
//       message: ChatRequest
//     }) => {
//       const chunks: any[] = []
//       for await (const chunk of apiClient.streamChat(conversationId, message)) {
//         chunks.push(chunk)
//         setStreamingMessage(chunk)
//       }
//       return chunks
//     },
//     onSuccess: (chunks, { conversationId }) => {
//       if (chunks.length > 0) {
//         const finalContent = chunks.map(c => c.content).join('')

//         // Add the complete message to the conversation
//         const newMessage: Message = {
//           id: `msg_${Date.now()}`,
//           conversationId,
//           role: 'assistant',
//           content: finalContent,
//           timestamp: new Date().toISOString(),
//           metadata: chunks[chunks.length - 1]?.metadata || {}
//         }

//         // This will be handled by the component that uses this hook
//       }
//     },
//     onError: (error: any) => {
//       setStreamingMessage(null)
//       toast.error('Streaming failed')
//     }
//   })
// }

// Agents Hooks
export function useAgents() {
  const setAgents = useSetAtom(agentsAtom)
  const setLoading = useSetAtom(agentsLoadingAtom)

  return useQuery({
    queryKey: queryKeys.agents,
    queryFn: () => apiClient.getAgents(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: true
  })
}

export function useAgent(id: string) {
  return useQuery({
    queryKey: queryKeys.agent(id),
    queryFn: () => apiClient.getAgent(id),
    enabled: !!id,
    staleTime: 10 * 60 * 1000, // 10 minutes
    retry: 2
  })
}

// Workspaces Hooks
export function useWorkspaces() {
  const setWorkspaces = useSetAtom(workspacesAtom)
  const setLoading = useSetAtom(workspacesLoadingAtom)

  return useQuery({
    queryKey: queryKeys.workspaces,
    queryFn: () => apiClient.getWorkspaces(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// Plugins Hooks
export function usePlugins() {
  const setPlugins = useSetAtom(pluginsAtom)
  const setLoading = useSetAtom(pluginsLoadingAtom)

  return useQuery({
    queryKey: queryKeys.plugins,
    queryFn: () => apiClient.getPlugins(),
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}

// Notifications Hooks
export function useNotifications() {
  const setNotifications = useSetAtom(notificationsAtom)
  const setLoading = useSetAtom(notificationsLoadingAtom)

  return useQuery({
    queryKey: queryKeys.notifications,
    queryFn: () => apiClient.getNotifications(),
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000 // Refetch every minute
  })
}

// Search Hooks
export function useSearch(query: string, filters?: SearchFilters) {
  const setResults = useSetAtom(searchResultsAtom)
  const setLoading = useSetAtom(searchLoadingAtom)

  return useQuery({
    queryKey: queryKeys.search(query, filters),
    queryFn: () => apiClient.searchGlobal(query),
    enabled: !!query && query.length > 2,
    staleTime: 60 * 1000, // 1 minute
    retry: 1
  })
}

// Health and Metrics Hooks
export function useHealth() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: () => apiClient.getHealthStatus(),
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Refetch every minute
    retry: 3
  })
}

export function useMetrics() {
  return useQuery({
    queryKey: queryKeys.metrics,
    queryFn: () => apiClient.getMetrics(),
    staleTime: 60 * 1000, // 1 minute
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
    retry: 2
  })
}

// File Upload Hooks
export function useFileUpload() {
  return useMutation({
    mutationFn: async ({ file }: { file: File }) => {
      const formData = new FormData()
      formData.append('file', file)

      const response = await apiClient.post('/api/files/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      return response.data
    },
  })
}

export function useMultipleFileUpload() {
  return useMutation({
    mutationFn: async ({ files }: { files: File[] }) => {
      const formData = new FormData()
      files.forEach((file, index) => {
        formData.append(`files[${index}]`, file)
      })

      const response = await apiClient.post('/api/files/upload-multiple', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      return response.data
    },
  })
}

// Voice Hooks
export function useTranscribeAudio() {
  return useMutation({
    mutationFn: (audioFile: File) => apiClient.transcribeAudio(audioFile),
    onSuccess: () => {
      toast.success('Audio transcribed successfully')
    },
    onError: (error: any) => {
      toast.error('Audio transcription failed')
    }
  })
}

export function useGenerateSpeech() {
  return useMutation({
    mutationFn: ({
      text,
      voiceSettings
    }: {
      text: string
      voiceSettings?: VoiceSettings
    }) => apiClient.generateSpeech(text, voiceSettings),
    onSuccess: () => {
      toast.success('Speech generated successfully')
    },
    onError: (error: any) => {
      toast.error('Speech generation failed')
    }
  })
}

// Settings Hooks
export function useSettings() {
  const { user, isLoading } = useUser()
  const settings = useAtomValue(settingsAtom)

  // Combine user preferences with general settings
  const combinedSettings = {
    ...settings,
    ...user?.preferences,
    name: user?.name || '',
    email: user?.email || '',
    avatar: user?.avatar || '',
    bio: user?.bio || '',
    apiKeys: user?.apiKeys || {}
  }

  return {
    data: combinedSettings,
    isLoading,
    error: null
  }
}

export function useUpdateSettings() {
  const queryClient = useQueryClient()
  const updatePreferences = useUser().updatePreferences
  const setSettings = useSetAtom(settingsAtom)

  return useMutation({
    mutationFn: async (updates: any) => {
      // Handle different types of updates
      if (updates.theme || updates.notifications || updates.privacy) {
        // User preferences update
        await updatePreferences(updates)
      } else {
        // General settings update
        setSettings(prev => ({ ...prev, ...updates }))
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.user })
    },
    onError: (error: any) => {
      toast.error('Failed to update settings')
    }
  })
}

// Export all hooks
export const hooks = {
  useAuth,
  useUser,
  useConversations,
  useConversation,
  useCreateConversation,
  useUpdateConversation,
  useDeleteConversation,
  useMessages,
  useInfiniteMessages,
  // useSendMessage, // Temporarily disabled
  // useStreamMessage, // Temporarily disabled
  useAgents,
  useAgent,
  useWorkspaces,
  usePlugins,
  useNotifications,
  useSearch,
  useHealth,
  useMetrics,
  useFileUpload,
  useMultipleFileUpload,
  useTranscribeAudio,
  useGenerateSpeech,
  useSettings,
  useUpdateSettings
}

// Voice hooks (separate from React Query)
export { useVoice } from './useVoice'
export { useVoiceOutput } from './useVoiceOutput'