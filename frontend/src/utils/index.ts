import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { format, formatDistanceToNow, parseISO } from 'date-fns'
import { v4 as uuidv4 } from 'uuid'
import type {
  Message,
  Conversation,
  User,
  Agent,
  ApiResponse,
  StreamingChunk,
  KeyboardShortcut
} from '@/types'

// Class name utility
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Date formatting utilities
export function formatMessageTime(timestamp: string): string {
  try {
    const date = parseISO(timestamp)
    const now = new Date()
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60)

    if (diffInHours < 24) {
      return formatDistanceToNow(date, { addSuffix: true })
    } else {
      return format(date, 'MMM d, h:mm a')
    }
  } catch {
    return timestamp
  }
}

export function formatConversationTime(timestamp: string): string {
  try {
    const date = parseISO(timestamp)
    return format(date, 'MMM d, yyyy')
  } catch {
    return timestamp
  }
}

export function formatRelativeTime(timestamp: string): string {
  try {
    const date = parseISO(timestamp)
    return formatDistanceToNow(date, { addSuffix: true })
  } catch {
    return timestamp
  }
}

// File utilities
export function getFileExtension(filename: string): string {
  return filename.split('.').pop()?.toLowerCase() || ''
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'

  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

export function isImageFile(filename: string): boolean {
  const imageExtensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg']
  return imageExtensions.includes(getFileExtension(filename))
}

// Text processing utilities
export function highlightText(text: string, searchTerm: string): string {
  if (!searchTerm || !text) return text

  // Use a safer approach to avoid ReDoS - split and join instead of RegExp
  const escapedTerm = searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const index = text.toLowerCase().indexOf(escapedTerm.toLowerCase())

  if (index === -1) return text

  const before = text.slice(0, index)
  const match = text.slice(index, index + searchTerm.length)
  const after = text.slice(index + searchTerm.length)

  return `${before}<mark>${match}</mark>${after}`
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength - 3) + '...'
}

export function countWords(text: string): number {
  return text.trim().split(/\s+/).filter(word => word.length > 0).length
}

export function countTokens(text: string): number {
  // Rough estimation: 1 token ≈ 4 characters for English text
  return Math.ceil(text.length / 4)
}

export function extractCodeBlocks(text: string): Array<{ language: string; code: string }> {
  const codeBlockRegex = /```(\w+)?\n?([\s\S]*?)\n?```/g
  const codeBlocks: Array<{ language: string; code: string }> = []
  let match

  while ((match = codeBlockRegex.exec(text)) !== null) {
    codeBlocks.push({
      language: match[1] || 'text',
      code: match[2].trim()
    })
  }

  return codeBlocks
}

export function stripMarkdown(text: string): string {
  // Remove markdown formatting
  return text
    .replace(/#{1,6}\s*/g, '') // Headers
    .replace(/\*\*(.*?)\*\*/g, '$1') // Bold
    .replace(/\*(.*?)\*/g, '$1') // Italic
    .replace(/`([^`]+)`/g, '$1') // Inline code
    .replace(/```[\s\S]*?```/g, '') // Code blocks
    .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1') // Links
    .replace(/!\[([^\]]+)\]\([^\)]+\)/g, '$1') // Images
    .replace(/^\s*[-*+]\s+/gm, '') // Lists
    .replace(/^\s*\d+\.\s+/gm, '') // Numbered lists
    .trim()
}

// Copy to clipboard utility
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await void void navigator.clipboard.writeText(text)
    return true
  } catch (error) {
    // Fallback for older browsers
    const textArea = document.createElement('textarea')
    textArea.value = text
    document.body.appendChild(textArea)
    textArea.select()
    try {
      document.execCommand('copy')
      return true
    } catch (fallbackError) {
      return false
    } finally {
      document.body.removeChild(textArea)
    }
  }
}

// API utilities
export function createApiResponse<T>(
  success: boolean,
  data?: T,
  error?: string,
  message?: string,
  metadata?: Record<string, unknown>
): ApiResponse<T> {
  return {
    success,
    data,
    error,
    message,
    metadata
  }
}

export function handleApiError(error: unknown): ApiResponse<null> {
  let errorMessage = 'An unexpected error occurred'
  let statusCode = 500

  const err = error as any // Type assertion for error handling
  if (err?.response) {
    // Server responded with error status
    statusCode = err.response.status
    errorMessage = err.response.data?.message || err.response.data?.error || errorMessage
  } else if (err?.request) {
    // Request was made but no response received
    errorMessage = 'Network error - please check your connection'
  } else if (err?.message) {
    // Something else happened
    errorMessage = err.message
  }

  logError(new Error(errorMessage), { statusCode, originalError: error })

  return createApiResponse(false, null, errorMessage)
}

export function createStreamingChunk(
  content: string,
  done: boolean = false,
  metadata?: Record<string, unknown>
): StreamingChunk {
  return {
    content,
    done,
    metadata: {
      tokens: content.split(' ').length,
      agent: typeof metadata?.agent === 'string' ? metadata.agent : undefined,
      confidence: typeof metadata?.confidence === 'number' ? metadata.confidence : undefined,
      ...metadata
    }
  }
}

// Error boundary utilities
export function logError(error: Error, context?: Record<string, unknown>) {
  console.error('Error occurred:', {
    message: error.message,
    stack: error.stack,
    context,
    timestamp: new Date().toISOString(),
    userAgent: typeof window !== 'undefined' ? window.navigator.userAgent : undefined
  })
}

// ID generation utilities
export function generateId(): string {
  return uuidv4()
}

export function generateConversationId(): string {
  return `conv_${generateId()}`
}

export function generateMessageId(): string {
  return `msg_${generateId()}`
}

// Validation utilities
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

export function isValidUrl(url: string): boolean {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

export function validatePassword(password: string): {
  isValid: boolean
  errors: string[]
} {
  const errors: string[] = []

  if (password.length < 8) {
    errors.push('Password must be at least 8 characters long')
  }

  if (!/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter')
  }

  if (!/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter')
  }

  if (!/\d/.test(password)) {
    errors.push('Password must contain at least one number')
  }

  if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
    errors.push('Password must contain at least one special character')
  }

  return {
    isValid: errors.length === 0,
    errors
  }
}
