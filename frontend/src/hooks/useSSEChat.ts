// Cartrita AI OS - SSE-first Chat Hook
// Primary SSE implementation with WebSocket fallback per spec

import { useState, useCallback, useRef, useEffect } from 'react'
import { useSetAtom, useAtomValue, useAtom } from 'jotai'
import { toast } from 'sonner'
import { apiClient } from '@/services/api'
import type { 
  ChatRequest, 
  ChatResponse, 
  Message, 
  StreamingCallbacks,
  SSEEvent 
} from '@/services/api'
import {
  streamingMessageAtom,
  currentMessagesAtom,
  currentConversationAtom,
  isStreamingAtom
} from '@/stores'
import { logError } from '@/utils'
import { generateChecksum, verifyFileIntegrity } from '@/utils/security'

export interface UseSSEChatOptions {
  enableStreaming?: boolean
  enableFallback?: boolean
  onError?: (error: Error) => void
  onComplete?: (response: ChatResponse) => void
  onAgentTask?: (taskId: string, status: string, progress?: number) => void
}

export interface UseSSEChatReturn {
  sendMessage: (request: ChatRequest) => Promise<void>
  sendMessageNonStreaming: (request: ChatRequest) => Promise<ChatResponse>
  isStreaming: boolean
  currentStream: { close: () => void } | null
  stopStreaming: () => void
  error: Error | null
  lastResponse: ChatResponse | null
}

export function useSSEChat(options: UseSSEChatOptions = {}): UseSSEChatReturn {
  const {
    enableStreaming = true,
    enableFallback = true,
    onError,
    onComplete,
    onAgentTask
  } = options

  // Atoms
  const [streamingMessage, setStreamingMessage] = useAtom(streamingMessageAtom) as [Message | null, (value: Message | null) => void]
  const currentMessages = useAtomValue(currentMessagesAtom)
  const currentConversation = useAtomValue(currentConversationAtom)

  // Local state
  const [error, setError] = useState<Error | null>(null)
  const [lastResponse, setLastResponse] = useState<ChatResponse | null>(null)
  
  // Refs for streaming control
  const currentStreamRef = useRef<{ close: () => void } | null>(null)
  const streamingContentRef = useRef<string>('')
  const agentTasksRef = useRef<Map<string, { status: string; progress: number }>>(new Map())

  // Clear error when starting new request
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  // Stop current streaming
  const stopStreaming = useCallback(() => {
    if (currentStreamRef.current) {
      currentStreamRef.current.close()
      currentStreamRef.current = null
    }
    setStreamingMessage(null)
  }, [setStreamingMessage])

  // Create streaming callbacks
  const createStreamingCallbacks = useCallback((request: ChatRequest): StreamingCallbacks => ({
    onToken: (content: string, delta?: string) => {
      if (delta) {
        streamingContentRef.current += delta
      } else {
        streamingContentRef.current = content
      }
      
      // Update streaming message atom
      setStreamingMessage({
        id: 'streaming',
        conversationId: request.conversation_id || currentConversation?.id || '',
        role: 'assistant',
        content: streamingContentRef.current,
        attachments: [],
        metadata: { streaming: true },
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        isEdited: false
      })
    },

    onFunctionCall: (functionName: string, args: unknown) => {
      console.log('Function call:', functionName, args)
      toast.info(`Calling ${functionName}...`)
    },

    onToolResult: (toolName: string, result: unknown) => {
      console.log('Tool result:', toolName, result)
      toast.success(`${toolName} completed`)
    },

    onAgentTaskStart: (taskId: string, agentType: string, description: string) => {
      agentTasksRef.current.set(taskId, { status: 'started', progress: 0 })
      onAgentTask?.(taskId, 'started', 0)
      toast.info(`Agent task started: ${description}`)
    },

    onAgentTaskProgress: (taskId: string, progress: number, status: string) => {
      const task = agentTasksRef.current.get(taskId)
      if (task) {
        task.progress = progress
        task.status = status
        onAgentTask?.(taskId, status, progress)
      }
    },

    onAgentTaskComplete: (taskId: string, result: unknown, success: boolean) => {
      agentTasksRef.current.delete(taskId)
      onAgentTask?.(taskId, success ? 'completed' : 'failed', 1)
      toast.success(`Agent task ${success ? 'completed' : 'failed'}`)
    },

    onMetrics: (metrics: unknown) => {
      console.log('Stream metrics:', metrics)
    },

    onError: (error: string, code: string, recoverable: boolean) => {
      const errorObj = new Error(`${code}: ${error}`)
      setError(errorObj)
      onError?.(errorObj)
      
      if (!recoverable) {
        stopStreaming()
      }
      
      toast.error(`Streaming error: ${error}`)
    },

    onDone: (finalResponse: string, metadata: unknown) => {
      // Create final response object
      const response: ChatResponse = {
        response: finalResponse,
        conversation_id: metadata.conversation_id || request.conversation_id || currentConversation?.id || '',
        agent_type: metadata.agent_type || 'supervisor',
        message: {
          id: metadata.message_id || crypto.randomUUID(),
          conversationId: metadata.conversation_id || request.conversation_id || currentConversation?.id || '',
          role: 'assistant',
          content: finalResponse,
          attachments: [],
          metadata: metadata || {},
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          isEdited: false,
          tokens: metadata.token_usage?.total_tokens,
          processingTime: metadata.processing_time
        },
        metadata: metadata,
        processing_time: metadata.processing_time,
        token_usage: metadata.token_usage,
        sources: metadata.sources || []
      }

      setLastResponse(response)
      onComplete?.(response)
      
      // Clean up streaming state
      setStreamingMessage(null)
      streamingContentRef.current = ''
      currentStreamRef.current = null
    }
  }), [currentConversation, setStreamingMessage, onError, onComplete, onAgentTask, stopStreaming])

  // Send streaming message (SSE primary, WebSocket fallback)
  const sendMessage = useCallback(async (request: ChatRequest) => {
    clearError()
    
    if (!enableStreaming) {
      throw new Error('Streaming is disabled')
    }

    try {
      // Stop any existing stream
      stopStreaming()
      
      // Reset streaming state
      streamingContentRef.current = ''
      setStreamingMessage({
        id: 'streaming',
        conversationId: request.conversation_id || currentConversation?.id || '',
        role: 'assistant',
        content: '',
        attachments: [],
        metadata: { streaming: true },
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        isEdited: false
      })

      // Create streaming callbacks
      const callbacks = createStreamingCallbacks(request)

      // Start streaming
      const stream = await apiClient.streamChat(request, callbacks)
      currentStreamRef.current = stream

    } catch (error) {
      const errorObj = error instanceof Error ? error : new Error('Unknown streaming error')
      setError(errorObj)
      onError?.(errorObj)
      setStreamingMessage(null)
      
      logError(errorObj, {
        context: 'sse_chat_error',
        request: {
          message: request.message.substring(0, 100),
          agent_override: request.agent_override,
          conversation_id: request.conversation_id
        }
      })
      
      throw errorObj
    }
  }, [enableStreaming, clearError, stopStreaming, setStreamingMessage, createStreamingCallbacks, onError])

  // Send non-streaming message
  const sendMessageNonStreaming = useCallback(async (request: ChatRequest): Promise<ChatResponse> => {
    clearError()
    
    try {
      setStreamingMessage({
        id: 'streaming',
        conversationId: request.conversation_id || currentConversation?.id || '',
        role: 'assistant',
        content: '',
        attachments: [],
        metadata: { streaming: true },
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        isEdited: false
      })
      
      // Use the new postChat method
      const response = await apiClient.postChat({
        ...request,
        stream: false
      })

      if (!response.success || !response.data) {
        throw new Error(response.error || 'Failed to send message')
      }

      setLastResponse(response.data)
      onComplete?.(response.data)
      
      return response.data

    } catch (error) {
      const errorObj = error instanceof Error ? error : new Error('Unknown chat error')
      setError(errorObj)
      onError?.(errorObj)
      
      logError(errorObj, {
        context: 'non_streaming_chat_error',
        request: {
          message: request.message.substring(0, 100),
          agent_override: request.agent_override,
          conversation_id: request.conversation_id
        }
      })
      
      throw errorObj
      
    } finally {
      setStreamingMessage(null)
    }
  }, [clearError, setStreamingMessage, onComplete, onError])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopStreaming()
    }
  }, [stopStreaming])

  // File integrity verification for sensitive operations
  useEffect(() => {
    const verifyIntegrity = async () => {
      try {
        const checksum = await generateChecksum('chat-endpoint')
        await verifyFileIntegrity('/api/chat', checksum)
      } catch (error) {
        logError(error as Error, {
          context: 'file_integrity_check_failed',
          component: 'useSSEChat'
        })
      }
    }
    
    verifyIntegrity()
  }, [])

  return {
    sendMessage,
    sendMessageNonStreaming,
    isStreaming: useAtomValue(isStreamingAtom),
    currentStream: currentStreamRef.current,
    stopStreaming,
    error,
    lastResponse
  }
}

// Convenience hook for simple chat interactions
export function useSimpleChat() {
  const { sendMessageNonStreaming, isStreaming, error } = useSSEChat({
    enableStreaming: false
  })

  const sendMessage = useCallback(async (message: string, agentOverride?: string) => {
    return sendMessageNonStreaming({
      message,
      agent_override: agentOverride as any,
      stream: false
    })
  }, [sendMessageNonStreaming])

  return {
    sendMessage,
    isLoading: isStreaming,
    error
  }
}

// Hook for streaming chat with progress tracking
export function useStreamingChat() {
  const [progress, setProgress] = useState<{ [taskId: string]: number }>({})
  
  const { sendMessage, isStreaming, error, stopStreaming } = useSSEChat({
    enableStreaming: true,
    onAgentTask: (taskId: string, status: string, progress?: number) => {
      setProgress(prev => ({
        ...prev,
        [taskId]: progress || 0
      }))
      
      if (status === 'completed' || status === 'failed') {
        setProgress(prev => {
          const { [taskId]: _, ...rest } = prev
          return rest
        })
      }
    }
  })

  return {
    sendMessage,
    isStreaming,
    error,
    stopStreaming,
    taskProgress: progress
  }
}