// Cartrita AI OS - Streaming Service
// Modern streaming implementation with proper error handling and reconnection

import type { ChatRequest, ChatResponse, StreamingChunk } from '@/types'

export interface StreamingOptions {
  onChunk?: (chunk: StreamingChunk) => void
  onComplete?: (response: ChatResponse) => void
  onError?: (error: Error) => void
  onAgentTask?: (taskId: string, status: string, progress?: number) => void
  baseUrl?: string
  timeout?: number
}

export class StreamingService {
  private baseUrl: string
  private controller: AbortController | null = null

  constructor(baseUrl: string = '') {
    // Use empty string for relative URLs in browser to use Next.js proxy
    this.baseUrl = baseUrl || (typeof window !== 'undefined' ? '' : 'http://localhost:8000')
  }

  /**
   * Send a streaming chat request using Server-Sent Events
   */
  async streamChat(request: ChatRequest, options: StreamingOptions = {}): Promise<void> {
    const {
      onChunk,
      onComplete,
      onError,
      onAgentTask,
      timeout = 60000
    } = options

    try {
      // Cancel any existing request
      this.cancelRequest()

      // Create new abort controller
      this.controller = new AbortController()

      // Prepare query parameters
      const params = new URLSearchParams({
        message: request.message,
        ...(request.conversation_id && { conversation_id: request.conversation_id }),
        ...(request.agent_override && { agent_override: request.agent_override }),
        ...(request.context && { context: JSON.stringify(request.context) })
      })

      const url = `${this.baseUrl}/api/chat/stream?${params}`

      // Create AbortController for timeout and cancellation
      const timeoutId = setTimeout(() => {
        if (this.controller && !this.controller.signal.aborted) {
          this.controller.abort('Request timeout')
        }
      }, timeout)

      // Create fetch request with timeout handling
      // Note: X-API-Key is added by the Next.js API route proxy
      console.log('Attempting to stream from:', url)
      const fetchPromise = fetch(url, {
        method: 'GET',
        headers: {
          'Accept': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        },
        signal: this.controller.signal,
      })

      try {
        const response = await fetchPromise
        
        // Clear timeout since request succeeded
        clearTimeout(timeoutId)

        if (!response.ok) {
          // Try to get error details from response body
          let errorMessage = `HTTP ${response.status}: ${response.statusText}`
          try {
            const errorBody = await response.text()
            if (errorBody) {
              const parsedError = JSON.parse(errorBody)
              
              // Special handling for backend unavailable
              if (parsedError.code === 'BACKEND_DOWN') {
                throw new Error('AI Backend Unavailable: The Cartrita AI service is not running. Please start the backend services with: docker compose up -d')
              }
              
              errorMessage += ` - ${parsedError.detail || parsedError.error || errorBody}`
            }
          } catch (parseError) {
            // Ignore JSON parsing errors, use default message
          }
          throw new Error(errorMessage)
        }

        if (!response.body) {
          throw new Error('No response body')
        }

        // Process the stream
        await this.processSSEStream(response.body, {
          onChunk,
          onComplete,
          onError,
          onAgentTask
        })
      } catch (fetchError) {
        clearTimeout(timeoutId)
        
        // Handle different error types appropriately
        if (fetchError instanceof Error) {
          if (fetchError.name === 'AbortError') {
            if (this.controller?.signal.reason === 'Request timeout') {
              throw new Error('Request timeout - server took too long to respond')
            }
            return // Request was cancelled by user
          }
          
          // More specific error handling for fetch failures
          if (fetchError instanceof TypeError && fetchError.message.includes('Failed to fetch')) {
            throw new Error('Connection failed: This may be due to proxy timeout, network issues, or CORS problems. The proxy timeout has been increased to 70s.')
          }
          
          throw fetchError
        }
        
        // More detailed error information for debugging
        console.error('Non-Error fetch failure:', fetchError)
        throw new Error(`Network error: ${JSON.stringify(fetchError) || 'Unknown fetch error'}`)
      }

    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        return // Request was cancelled
      }
      
      console.error('Streaming error:', error)
      onError?.(error instanceof Error ? error : new Error('Unknown streaming error'))
    } finally {
      this.controller = null
    }
  }

  /**
   * Send a voice chat request using Server-Sent Events
   */
  async streamVoiceChat(
    conversationId: string,
    transcribedText: string,
    conversationHistory: unknown[] = [],
    options: StreamingOptions = {}
  ): Promise<void> {
    const {
      onChunk,
      onComplete,
      onError,
      onAgentTask,
      timeout = 60000
    } = options

    try {
      this.cancelRequest()
      this.controller = new AbortController()

      const params = new URLSearchParams({
        conversationId,
        transcribedText,
        conversationHistory: JSON.stringify(conversationHistory)
      })

      const url = `${this.baseUrl}/api/chat/voice/stream?${params}`

      // Create AbortController for timeout and cancellation
      const timeoutId = setTimeout(() => {
        if (this.controller && !this.controller.signal.aborted) {
          this.controller.abort('Voice request timeout')
        }
      }, timeout)

      const fetchPromise = fetch(url, {
        method: 'GET',
        headers: {
          'Accept': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        },
        signal: this.controller.signal,
      })

      try {
        const response = await fetchPromise
        
        // Clear timeout since request succeeded
        clearTimeout(timeoutId)

        if (!response.ok) {
          // Try to get error details from response body
          let errorMessage = `HTTP ${response.status}: ${response.statusText}`
          try {
            const errorBody = await response.text()
            if (errorBody) {
              const parsedError = JSON.parse(errorBody)
              
              // Special handling for backend unavailable
              if (parsedError.code === 'BACKEND_DOWN') {
                throw new Error('AI Backend Unavailable: The Cartrita AI service is not running. Please start the backend services with: docker compose up -d')
              }
              
              errorMessage += ` - ${parsedError.detail || parsedError.error || errorBody}`
            }
          } catch (parseError) {
            // Ignore JSON parsing errors, use default message
          }
          throw new Error(errorMessage)
        }

        if (!response.body) {
          throw new Error('No response body')
        }

        await this.processSSEStream(response.body, {
          onChunk,
          onComplete,
          onError,
          onAgentTask
        })
      } catch (fetchError) {
        clearTimeout(timeoutId)
        
        // Handle different error types appropriately
        if (fetchError instanceof Error) {
          if (fetchError.name === 'AbortError') {
            if (this.controller?.signal.reason === 'Voice request timeout') {
              throw new Error('Voice request timeout - server took too long to respond')
            }
            return // Request was cancelled by user
          }
          throw fetchError
        }
        throw new Error('Unknown fetch error')
      }

    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        return
      }
      
      console.error('Voice streaming error:', error)
      onError?.(error instanceof Error ? error : new Error('Unknown voice streaming error'))
    } finally {
      this.controller = null
    }
  }

  /**
   * Send a non-streaming chat request
   */
  async sendChat(request: ChatRequest): Promise<ChatResponse> {
    try {
      this.cancelRequest()
      this.controller = new AbortController()

      const response = await fetch(`${this.baseUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
        signal: this.controller.signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      
      if (!data.success && data.error) {
        throw new Error(data.error)
      }

      return data as ChatResponse

    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Request was cancelled')
      }
      
      console.error('Chat error:', error)
      throw error instanceof Error ? error : new Error('Unknown chat error')
    } finally {
      this.controller = null
    }
  }

  /**
   * Send a non-streaming voice chat request
   */
  async sendVoiceChat(
    conversationId: string,
    transcribedText: string,
    conversationHistory: unknown[] = []
  ): Promise<ChatResponse> {
    try {
      this.cancelRequest()
      this.controller = new AbortController()

      const response = await fetch(`${this.baseUrl}/api/chat/voice`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          conversationId,
          transcribedText,
          conversationHistory,
          voiceMode: true
        }),
        signal: this.controller.signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      return data as ChatResponse

    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Voice request was cancelled')
      }
      
      console.error('Voice chat error:', error)
      throw error instanceof Error ? error : new Error('Unknown voice chat error')
    } finally {
      this.controller = null
    }
  }

  /**
   * Cancel the current request
   */
  cancelRequest(): void {
    if (this.controller) {
      this.controller.abort()
      this.controller = null
    }
  }

  /**
   * Process Server-Sent Events stream
   */
  private async processSSEStream(
    body: ReadableStream<Uint8Array>,
    callbacks: {
      onChunk?: (chunk: StreamingChunk) => void
      onComplete?: (response: ChatResponse) => void
      onError?: (error: Error) => void
      onAgentTask?: (taskId: string, status: string, progress?: number) => void
    }
  ): Promise<void> {
    if (!body) {
      callbacks.onError?.(new Error('No response body to process'))
      return
    }

    const reader = body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let completeResponse = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        
        if (done) {
          break
        }

        // Decode the chunk
        buffer += decoder.decode(value, { stream: true })
        
        // Process complete lines
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.trim() === '') continue

          // Handle SSE format
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim() // Remove 'data: ' prefix and trim whitespace

            if (data === '[DONE]') {
              // Stream complete
              if (callbacks.onComplete) {
                callbacks.onComplete({
                  response: completeResponse,
                  conversation_id: '',
                  agent_type: 'supervisor'
                } as ChatResponse)
              }
              return
            }

            // Skip empty data
            if (!data) {
              continue
            }

            try {
              // Validate JSON before parsing
              if (!data || data.trim() === '') {
                continue
              }
              
              const parsed = JSON.parse(data)

              // Handle different event types
              if (parsed.type === 'content' || parsed.content) {
                const chunk: StreamingChunk = {
                  content: parsed.content || parsed.response || '',
                  done: false,
                  metadata: parsed.metadata || {}
                }

                completeResponse += chunk.content
                callbacks.onChunk?.(chunk)
              } else if (parsed.type === 'agent_task_started') {
                callbacks.onAgentTask?.(parsed.taskId, 'started')
              } else if (parsed.type === 'agent_task_progress') {
                callbacks.onAgentTask?.(parsed.taskId, 'progress', parsed.progress)
              } else if (parsed.type === 'agent_task_complete') {
                callbacks.onAgentTask?.(parsed.taskId, 'completed')
              } else if (parsed.error) {
                const errorMessage = parsed.details || parsed.error || 'Unknown streaming error'
                callbacks.onError?.(new Error(errorMessage))
                return
              } else {
                // Handle complete response object (when backend sends full ChatResponse)
                if (parsed.response && typeof parsed.response === 'string') {
                  // This is the expected response format from backend
                  const fullResponse = parsed.response
                  completeResponse = fullResponse
                  
                  // For large responses, emit as streaming chunks for better UX
                  if (fullResponse.length > 100) {
                    const chunkSize = 20 // Characters per chunk
                    let currentPos = 0
                    
                    const emitNextChunk = () => {
                      if (currentPos < fullResponse.length) {
                        const chunkContent = fullResponse.slice(currentPos, currentPos + chunkSize)
                        callbacks.onChunk?.({
                          content: chunkContent,
                          done: false,
                          metadata: parsed.metadata || {}
                        })
                        currentPos += chunkSize
                        
                        // Use setTimeout to avoid blocking the UI
                        setTimeout(emitNextChunk, 50)
                      } else {
                        // All chunks emitted, now complete
                        if (callbacks.onComplete) {
                          const chatResponse: ChatResponse = {
                            response: parsed.response,
                            conversation_id: parsed.conversation_id || '',
                            agent_type: parsed.agent_type || 'supervisor',
                            message: parsed.message,
                            metadata: parsed.metadata || {},
                            processing_time: parsed.processing_time,
                            token_usage: parsed.token_usage,
                            sources: parsed.sources || []
                          }
                          callbacks.onComplete(chatResponse)
                        }
                      }
                    }
                    
                    emitNextChunk()
                  } else {
                    // Small response, emit immediately
                    callbacks.onChunk?.({
                      content: fullResponse,
                      done: false,
                      metadata: parsed.metadata || {}
                    })
                    
                    if (callbacks.onComplete) {
                      const chatResponse: ChatResponse = {
                        response: parsed.response,
                        conversation_id: parsed.conversation_id || '',
                        agent_type: parsed.agent_type || 'supervisor',
                        message: parsed.message,
                        metadata: parsed.metadata || {},
                        processing_time: parsed.processing_time,
                        token_usage: parsed.token_usage,
                        sources: parsed.sources || []
                      }
                      callbacks.onComplete(chatResponse)
                    }
                  }
                } else {
                  // Fallback: treat as complete response
                  completeResponse = parsed.response || JSON.stringify(parsed)
                  if (callbacks.onComplete) {
                    callbacks.onComplete(parsed as ChatResponse)
                  }
                }
                return
              }

            } catch (parseError) {
              // More detailed error logging for debugging
              console.warn('Failed to parse SSE data:', {
                data: data.substring(0, 200), // Limit logged data length
                error: parseError instanceof Error ? parseError.message : String(parseError)
              })
              // Don't stop the stream for parsing errors, just warn and continue
            }
          }
        }
      }

    } catch (error) {
      console.error('Stream processing error:', error)
      const errorMessage = error instanceof Error ? error.message : 'Stream processing failed'
      callbacks.onError?.(new Error(`Streaming failed: ${errorMessage}`))
    } finally {
      try {
        reader.releaseLock()
      } catch (lockError) {
        console.warn('Failed to release reader lock:', lockError)
      }
    }
  }


  /**
   * Check if a request is currently active
   */
  get isActive(): boolean {
    return this.controller !== null
  }
}

// Export singleton instance
export const streamingService = new StreamingService()

// Export interface for convenience
export interface StreamingServiceOptions extends StreamingOptions {}