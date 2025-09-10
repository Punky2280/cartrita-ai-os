// Cartrita AI OS - SSE Chat Hooks Tests
// Tests for SSE-first chat hooks with comprehensive coverage

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import React from 'react'
import { Provider as JotaiProvider } from 'jotai'
import { useSSEChat, useSimpleChat, useStreamingChat } from '@/hooks/useSSEChat'
import type { ChatRequest, ChatResponse } from '@/services/api'

// Mock the API client
const mockStreamChat = vi.fn()
const mockPostChat = vi.fn()
const mockStreamChatSSE = vi.fn()
const mockStreamChatWebSocket = vi.fn()

vi.mock('@/services/api', () => ({
  apiClient: {
    streamChat: mockStreamChat,
    postChat: mockPostChat,
    streamChatSSE: mockStreamChatSSE,
    streamChatWebSocket: mockStreamChatWebSocket
  }
}))

// Mock atoms
const mockSetIsStreaming = vi.fn()
const mockSetStreamingMessage = vi.fn()
const mockCurrentMessages = []
const mockCurrentConversation = {
  id: 'conv_test_123',
  title: 'Test Conversation'
}

vi.mock('@/stores', () => ({
  isStreamingAtom: {},
  streamingMessageAtom: {},
  currentMessagesAtom: {},
  currentConversationAtom: {}
}))

vi.mock('jotai', () => ({
  useSetAtom: (atom: unknown) => {
    if (atom === 'isStreamingAtom') return mockSetIsStreaming
    if (atom === 'streamingMessageAtom') return mockSetStreamingMessage
    return vi.fn()
  },
  useAtomValue: (atom: unknown) => {
    if (atom === 'currentMessagesAtom') return mockCurrentMessages
    if (atom === 'currentConversationAtom') return mockCurrentConversation
    if (atom === 'isStreamingAtom') return false
    return undefined
  }
}))

// Mock utilities
vi.mock('@/utils', () => ({
  logError: vi.fn(),
  generateChecksum: vi.fn().mockResolvedValue('mock-checksum'),
  verifyFileIntegrity: vi.fn().mockResolvedValue(true)
}))

vi.mock('@/utils/security', () => ({
  generateChecksum: vi.fn().mockResolvedValue('mock-checksum'),
  verifyFileIntegrity: vi.fn().mockResolvedValue(true)
}))

// Mock toast notifications
vi.mock('sonner', () => ({
  toast: {
    info: vi.fn(),
    success: vi.fn(),
    error: vi.fn()
  }
}))

describe('useSSEChat', () => {
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <JotaiProvider>{children}</JotaiProvider>
  )

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Non-streaming mode', () => {
    it('should send non-streaming message successfully', async () => {
      const mockResponse: ChatResponse = {
        response: 'Test response',
        conversation_id: 'conv_123',
        agent_type: 'supervisor',
        processing_time: 1.5,
        token_usage: { total_tokens: 25 },
        message: {
          id: 'msg_123',
          conversationId: 'conv_123',
          role: 'assistant',
          content: 'Test response',
          attachments: [],
          metadata: {},
          createdAt: '2024-01-01T00:00:00Z',
          updatedAt: '2024-01-01T00:00:00Z',
          isEdited: false
        }
      }

      mockPostChat.mockResolvedValue({
        success: true,
        data: mockResponse
      })

      const mockOnComplete = vi.fn()
      const mockOnError = vi.fn()

      const { result } = renderHook(
        () => useSSEChat({
          enableStreaming: false,
          onComplete: mockOnComplete,
          onError: mockOnError
        }),
        { wrapper }
      )

      const request: ChatRequest = {
        message: 'Hello, world!',
        agent_override: 'supervisor'
      }

      await act(async () => {
        await result.current.sendMessageNonStreaming(request)
      })

      expect(mockPostChat).toHaveBeenCalledWith({
        ...request,
        stream: false
      })
      expect(mockOnComplete).toHaveBeenCalledWith(mockResponse)
      expect(mockOnError).not.toHaveBeenCalled()
      expect(result.current.lastResponse).toEqual(mockResponse)
    })

    it('should handle non-streaming errors', async () => {
      const mockError = new Error('API Error')
      mockPostChat.mockRejectedValue(mockError)

      const mockOnComplete = vi.fn()
      const mockOnError = vi.fn()

      const { result } = renderHook(
        () => useSSEChat({
          enableStreaming: false,
          onComplete: mockOnComplete,
          onError: mockOnError
        }),
        { wrapper }
      )

      const request: ChatRequest = {
        message: 'This will fail'
      }

      await act(async () => {
        try {
          await result.current.sendMessageNonStreaming(request)
        } catch (error) {
          expect(error).toBe(mockError)
        }
      })

      expect(mockOnError).toHaveBeenCalledWith(mockError)
      expect(mockOnComplete).not.toHaveBeenCalled()
      expect(result.current.error).toBe(mockError)
    })
  })

  describe('Streaming mode', () => {
    it('should initiate streaming chat successfully', async () => {
      const mockStream = {
        close: vi.fn(),
        conversationId: 'conv_streaming_123'
      }

      mockStreamChat.mockResolvedValue(mockStream)

      const mockCallbacks = {
        onToken: vi.fn(),
        onDone: vi.fn(),
        onError: vi.fn()
      }

      const { result } = renderHook(
        () => useSSEChat({
          enableStreaming: true,
          onComplete: mockCallbacks.onDone,
          onError: mockCallbacks.onError
        }),
        { wrapper }
      )

      const request: ChatRequest = {
        message: 'Stream this message',
        agent_override: 'research'
      }

      await act(async () => {
        await result.current.sendMessage(request)
      })

      expect(mockSetIsStreaming).toHaveBeenCalledWith(true)
      expect(mockStreamChat).toHaveBeenCalledWith(request, expect.any(Object))
      expect(result.current.currentStream).toBe(mockStream)
    })

    it('should handle streaming token events', async () => {
      let capturedCallbacks: unknown

      mockStreamChat.mockImplementation((request, callbacks) => {
        capturedCallbacks = callbacks
        return Promise.resolve({
          close: vi.fn(),
          conversationId: 'conv_123'
        })
      })

      const { result } = renderHook(() => useSSEChat({ enableStreaming: true }), {
        wrapper
      })

      await act(async () => {
        await result.current.sendMessage({
          message: 'Test streaming'
        })
      })

      // Simulate token events
      act(() => {
        capturedCallbacks.onToken('Hello', 'Hello')
      })

      act(() => {
        capturedCallbacks.onToken('Hello there', ' there')
      })

      expect(mockSetStreamingMessage).toHaveBeenCalledWith(
        expect.objectContaining({
          content: 'Hello'
        })
      )

      expect(mockSetStreamingMessage).toHaveBeenCalledWith(
        expect.objectContaining({
          content: 'Hello there'
        })
      )
    })

    it('should handle streaming completion', async () => {
      let capturedCallbacks: unknown

      mockStreamChat.mockImplementation((request, callbacks) => {
        capturedCallbacks = callbacks
        return Promise.resolve({
          close: vi.fn(),
          conversationId: 'conv_123'
        })
      })

      const mockOnComplete = vi.fn()

      const { result } = renderHook(
        () => useSSEChat({
          enableStreaming: true,
          onComplete: mockOnComplete
        }),
        { wrapper }
      )

      await act(async () => {
        await result.current.sendMessage({
          message: 'Test completion'
        })
      })

      const mockFinalResponse = 'Final streaming response'
      const mockMetadata = {
        conversation_id: 'conv_123',
        agent_type: 'supervisor',
        processing_time: 2.1,
        token_usage: { total_tokens: 30 }
      }

      // Simulate completion event
      act(() => {
        capturedCallbacks.onDone(mockFinalResponse, mockMetadata)
      })

      expect(mockSetIsStreaming).toHaveBeenCalledWith(false)
      expect(mockSetStreamingMessage).toHaveBeenCalledWith(null)
      expect(mockOnComplete).toHaveBeenCalledWith(
        expect.objectContaining({
          response: mockFinalResponse,
          conversation_id: 'conv_123',
          agent_type: 'supervisor'
        })
      )
    })

    it('should handle agent task events', async () => {
      let capturedCallbacks: unknown

      mockStreamChat.mockImplementation((request, callbacks) => {
        capturedCallbacks = callbacks
        return Promise.resolve({
          close: vi.fn(),
          conversationId: 'conv_123'
        })
      })

      const mockOnAgentTask = vi.fn()

      const { result } = renderHook(
        () => useSSEChat({
          enableStreaming: true,
          onAgentTask: mockOnAgentTask
        }),
        { wrapper }
      )

      await act(async () => {
        await result.current.sendMessage({
          message: 'Task with agent events'
        })
      })

      // Simulate agent task events
      act(() => {
        capturedCallbacks.onAgentTaskStart('task_1', 'task', 'Processing task')
      })

      act(() => {
        capturedCallbacks.onAgentTaskProgress('task_1', 0.5, 'halfway')
      })

      act(() => {
        capturedCallbacks.onAgentTaskComplete('task_1', 'Task completed', true)
      })

      expect(mockOnAgentTask).toHaveBeenCalledWith('task_1', 'started', 0)
      expect(mockOnAgentTask).toHaveBeenCalledWith('task_1', 'halfway', 0.5)
      expect(mockOnAgentTask).toHaveBeenCalledWith('task_1', 'completed', 1)
    })

    it('should stop streaming when requested', async () => {
      const mockStream = {
        close: vi.fn(),
        conversationId: 'conv_123'
      }

      mockStreamChat.mockResolvedValue(mockStream)

      const { result } = renderHook(() => useSSEChat({ enableStreaming: true }), {
        wrapper
      })

      await act(async () => {
        await result.current.sendMessage({
          message: 'Stream to be stopped'
        })
      })

      expect(result.current.currentStream).toBe(mockStream)

      act(() => {
        result.current.stopStreaming()
      })

      expect(mockStream.close).toHaveBeenCalled()
      expect(mockSetIsStreaming).toHaveBeenCalledWith(false)
      expect(mockSetStreamingMessage).toHaveBeenCalledWith(null)
      expect(result.current.currentStream).toBeNull()
    })
  })

  describe('Error handling', () => {
    it('should handle streaming errors gracefully', async () => {
      const mockError = new Error('Streaming failed')
      mockStreamChat.mockRejectedValue(mockError)

      const mockOnError = vi.fn()

      const { result } = renderHook(
        () => useSSEChat({
          enableStreaming: true,
          onError: mockOnError
        }),
        { wrapper }
      )

      await act(async () => {
        try {
          await result.current.sendMessage({
            message: 'This will fail'
          })
        } catch (error) {
          expect(error).toBe(mockError)
        }
      })

      expect(mockOnError).toHaveBeenCalledWith(mockError)
      expect(mockSetIsStreaming).toHaveBeenCalledWith(false)
      expect(result.current.error).toBe(mockError)
    })

    it('should clear errors on new requests', async () => {
      const { result } = renderHook(() => useSSEChat({ enableStreaming: false }), {
        wrapper
      })

      // Set initial error
      act(() => {
        ;(result.current as any).setError(new Error('Previous error'))
      })

      // Mock successful response
      mockPostChat.mockResolvedValue({
        success: true,
        data: {
          response: 'Success',
          conversation_id: 'conv_123',
          agent_type: 'supervisor'
        }
      })

      await act(async () => {
        await result.current.sendMessageNonStreaming({
          message: 'New request'
        })
      })

      expect(result.current.error).toBeNull()
    })
  })
})

describe('useSimpleChat', () => {
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <JotaiProvider>{children}</JotaiProvider>
  )

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should send simple message without streaming', async () => {
    const mockResponse: ChatResponse = {
      response: 'Simple response',
      conversation_id: 'conv_simple_123',
      agent_type: 'supervisor'
    }

    mockPostChat.mockResolvedValue({
      success: true,
      data: mockResponse
    })

    const { result } = renderHook(() => useSimpleChat(), { wrapper })

    await act(async () => {
      const response = await result.current.sendMessage('Hello', 'research')
      expect(response).toEqual(mockResponse)
    })

    expect(mockPostChat).toHaveBeenCalledWith({
      message: 'Hello',
      agent_override: 'research',
      stream: false
    })
    expect(result.current.error).toBeNull()
  })

  it('should handle simple chat errors', async () => {
    const mockError = new Error('Simple chat error')
    mockPostChat.mockRejectedValue(mockError)

    const { result } = renderHook(() => useSimpleChat(), { wrapper })

    await act(async () => {
      try {
        await result.current.sendMessage('This will fail')
      } catch (error) {
        expect(error).toBe(mockError)
      }
    })

    expect(result.current.error).toBe(mockError)
  })
})

describe('useStreamingChat', () => {
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <JotaiProvider>{children}</JotaiProvider>
  )

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should track task progress during streaming', async () => {
    let capturedCallbacks: unknown

    mockStreamChat.mockImplementation((request, callbacks) => {
      capturedCallbacks = callbacks
      return Promise.resolve({
        close: vi.fn(),
        conversationId: 'conv_123'
      })
    })

    const { result } = renderHook(() => useStreamingChat(), { wrapper })

    await act(async () => {
      await result.current.sendMessage({
        message: 'Task with progress'
      })
    })

    // Simulate agent task progress
    act(() => {
      capturedCallbacks.onAgentTask('task_progress_1', 'started', 0)
    })

    act(() => {
      capturedCallbacks.onAgentTask('task_progress_1', 'processing', 0.3)
    })

    act(() => {
      capturedCallbacks.onAgentTask('task_progress_1', 'processing', 0.7)
    })

    act(() => {
      capturedCallbacks.onAgentTask('task_progress_1', 'completed', 1)
    })

    expect(result.current.taskProgress).toEqual({
      task_progress_1: 1
    })

    // Task should be removed from progress after completion
    await waitFor(() => {
      expect(result.current.taskProgress).toEqual({})
    })
  })

  it('should handle multiple concurrent tasks', async () => {
    let capturedCallbacks: unknown

    mockStreamChat.mockImplementation((request, callbacks) => {
      capturedCallbacks = callbacks
      return Promise.resolve({
        close: vi.fn(),
        conversationId: 'conv_123'
      })
    })

    const { result } = renderHook(() => useStreamingChat(), { wrapper })

    await act(async () => {
      await result.current.sendMessage({
        message: 'Multiple tasks'
      })
    })

    // Start multiple tasks
    act(() => {
      capturedCallbacks.onAgentTask('task_1', 'started', 0)
      capturedCallbacks.onAgentTask('task_2', 'started', 0)
      capturedCallbacks.onAgentTask('task_3', 'started', 0)
    })

    // Update progress
    act(() => {
      capturedCallbacks.onAgentTask('task_1', 'processing', 0.5)
      capturedCallbacks.onAgentTask('task_2', 'processing', 0.8)
      capturedCallbacks.onAgentTask('task_3', 'processing', 0.2)
    })

    expect(result.current.taskProgress).toEqual({
      task_1: 0.5,
      task_2: 0.8,
      task_3: 0.2
    })

    // Complete one task
    act(() => {
      capturedCallbacks.onAgentTask('task_1', 'completed', 1)
    })

    await waitFor(() => {
      expect(result.current.taskProgress).toEqual({
        task_2: 0.8,
        task_3: 0.2
      })
    })
  })
})