// Cartrita AI OS - Message Bubble Component
// Enhanced message display with ChatGPT-like sty      // Use ReactMarkdown for safe renderings

'use client'

import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import {
  Copy,
  ThumbsUp,
  ThumbsDown,
  RotateCcw,
  Edit3,
  X,
  Bot,
  User as UserIcon,
  Clock,
  CheckCircle,
  AlertCircle,
  MoreVertical,
  Share,
  Download,
  Check,
  Trash2
} from 'lucide-react'
import { cn, formatMessageTime, copyToClipboard } from '@/utils'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui'
import { Badge } from '@/components/ui'
import { Textarea } from '@/components/ui'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui'
import { useUser } from '@/hooks'
import type { Message } from '@/types'

// Message content renderer with markdown support
function MessageContent({
  content,
  isUser,
  isStreaming = false
}: {
  content: string
  isUser: boolean
  isStreaming?: boolean
}) {
  // Simple markdown-like rendering
  const renderContent = (text: string) => {
    // Code blocks
    const codeBlockRegex = /```(\w+)?\n?([\s\S]*?)```/g
    const parts: Array<{ type: 'text' | 'code', content: string, language?: string }> = []
    let lastIndex = 0
    let match

    while ((match = codeBlockRegex.exec(text)) !== null) {
      // Add text before code block
      if (match.index > lastIndex) {
        parts.push({
          type: 'text',
          content: text.slice(lastIndex, match.index)
        })
      }

      // Add code block
      parts.push({
        type: 'code',
        content: match[2].trim(),
        language: match[1] || 'text'
      })

      lastIndex = match.index + match[0].length
    }

    // Add remaining text
    if (lastIndex < text.length) {
      parts.push({
        type: 'text',
        content: text.slice(lastIndex)
      })
    }

    return parts.map((part, index) => {
      if (part.type === 'code') {
        return (
          <pre key={index} className="bg-muted p-4 rounded-lg overflow-x-auto my-2">
            <SyntaxHighlighter
              language={part.language}
              style={oneDark as any}
              className="rounded-md"
            >
              {part.content}
            </SyntaxHighlighter>
          </pre>
        )
      }

      // Simple text formatting
      const formattedText = part.content
        .split('\n')
        .map((line, lineIndex) => {
          // Bold
          line = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
          // Italic
          line = line.replace(/\*(.*?)\*/g, '<em>$1</em>')
          // Inline code
          line = line.replace(/`([^`]+)`/g, '<code class="bg-muted px-1 py-0.5 rounded text-sm">$1</code>')

          return lineIndex === 0 ? line : `<br />${line}`
        })
        .join('')

      return (
        <div key={index} className="prose prose-sm dark:prose-invert max-w-none">
          <ReactMarkdown
            components={{
              code: ({ node, className, children, ...props }: any) => {
                const match = /language-(\w+)/.exec(className || '')
                return !props.inline && match ? (
                  <SyntaxHighlighter
                    style={oneDark as any}
                    language={match[1]}
                    PreTag="div"
                    className="rounded-md"
                    {...props}
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                ) : (
                  <code className="bg-muted px-1 py-0.5 rounded text-sm" {...props}>
                    {children}
                  </code>
                )
              }
            }}
          >
            {part.content}
          </ReactMarkdown>
        </div>
      )
    })
  }

  return (
    <div className={cn(
      'prose prose-sm dark:prose-invert max-w-none',
      isUser ? 'text-white' : 'text-foreground'
    )}>
      <div className={isStreaming ? 'streaming-text' : ''}>
        {renderContent(content)}
      </div>
    </div>
  )
}

// Main Message Bubble Component
interface MessageBubbleProps {
  message: Message
  isUser: boolean
  showAvatar?: boolean
  showTimestamp?: boolean
  showActions?: boolean
  isStreaming?: boolean
  onEdit?: (messageId: string, newContent: string) => void
  onDelete?: (messageId: string) => void
  onRegenerate?: (messageId: string) => void
  onFeedback?: (messageId: string, feedback: 'positive' | 'negative') => void
}

export function MessageBubble({
  message,
  isUser,
  showAvatar = true,
  showTimestamp = true,
  showActions = true,
  isStreaming = false,
  onEdit,
  onDelete,
  onRegenerate,
  onFeedback
}: MessageBubbleProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editContent, setEditContent] = useState(message.content)
  const [showFeedback, setShowFeedback] = useState(false)
  const { user } = useUser()

  const editTextareaRef = useRef<HTMLTextAreaElement>(null)

  // Focus textarea when editing starts
  useEffect(() => {
    if (isEditing && editTextareaRef.current) {
      editTextareaRef.current.focus()
      editTextareaRef.current.setSelectionRange(editContent.length, editContent.length)
    }
  }, [isEditing, editContent])

  // Handle copy message
  const handleCopy = async () => {
    const success = await copyToClipboard(message.content)
    if (success) {
      toast.success('Message copied to clipboard')
    } else {
      toast.error('Failed to copy message')
    }
  }

  // Handle edit save
  const handleEditSave = () => {
    if (editContent.trim() && editContent !== message.content) {
      onEdit?.(message.id, editContent.trim())
    }
    setIsEditing(false)
  }

  // Handle edit cancel
  const handleEditCancel = () => {
    setEditContent(message.content)
    setIsEditing(false)
  }

  // Handle feedback
  const handleFeedback = (feedback: 'positive' | 'negative') => {
    onFeedback?.(message.id, feedback)
    setShowFeedback(true)
    toast.success(`Feedback recorded: ${feedback === 'positive' ? '👍' : '👎'}`)
  }

  // Get message status
  const getMessageStatus = () => {
    if (message.metadata?.error) return 'error'
    if (message.metadata?.processing) return 'processing'
    return 'success'
  }

  const status = getMessageStatus()

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'group flex gap-3 max-w-[80%]',
        isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'
      )}
    >
      {/* Avatar */}
      {showAvatar && (
        <Avatar className="h-8 w-8 flex-shrink-0">
          {isUser ? (
            <>
              <AvatarImage src={user?.avatar} />
              <AvatarFallback>
                <UserIcon className="h-4 w-4" />
              </AvatarFallback>
            </>
          ) : (
            <AvatarFallback>
              <Bot className="h-4 w-4" />
            </AvatarFallback>
          )}
        </Avatar>
      )}

      {/* Message Content */}
      <div className={cn(
        'flex flex-col gap-2',
        isUser ? 'items-end' : 'items-start'
      )}>
        {/* Message Bubble */}
        <div className={cn(
          'relative px-4 py-3 rounded-2xl max-w-full break-words message-bubble-enter fluid-hover',
          isUser
            ? 'gradient-user-message text-white rounded-br-md'
            : 'glass-morphism gradient-ai-message text-foreground rounded-bl-md',
          status === 'error' && 'border border-destructive',
          status === 'processing' && 'animate-pulse',
          isStreaming && 'streaming-text'
        )}>
          {/* Status Indicator */}
          {status === 'error' && (
            <div className="flex items-center gap-2 mb-2 text-destructive">
              <AlertCircle className="h-4 w-4" />
              <span className="text-sm">Error processing message</span>
            </div>
          )}

          {status === 'processing' && (
            <div className="flex items-center gap-2 mb-2 text-muted-foreground">
              <Clock className="h-4 w-4" />
              <span className="text-sm">Processing...</span>
            </div>
          )}

          {/* Message Content */}
          {isEditing ? (
            <Textarea
              ref={editTextareaRef}
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              className="min-h-[60px] bg-transparent border-none p-0 resize-none focus:ring-0"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleEditSave()
                }
                if (e.key === 'Escape') {
                  handleEditCancel()
                }
              }}
            />
          ) : (
            <MessageContent
              content={message.content}
              isUser={isUser}
              isStreaming={isStreaming}
            />
          )}

          {/* Edit Actions */}
          {isEditing && (
            <div className="flex items-center gap-2 mt-2">
              <button
                onClick={handleEditSave}
                className="h-6 px-2"
              >
                <Check className="h-3 w-3" />
              </button>
              <button
                onClick={handleEditCancel}
                className="h-6 px-2"
              >
                <X className="h-3 w-3" />
              </button>
            </div>
          )}

          {/* Message Actions */}
          {showActions && !isEditing && (
            <div className={cn(
              'absolute top-0 opacity-0 group-hover:opacity-100 transition-opacity',
              'flex items-center gap-1',
              isUser ? '-left-12' : '-right-12'
            )}>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      onClick={handleCopy}
                      className="h-6 w-6 p-0 bg-transparent hover:bg-accent rounded"
                    >
                      <Copy className="h-3 w-3" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>Copy message</TooltipContent>
                </Tooltip>

                {!isUser && !showFeedback && (
                  <>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <button
                          onClick={() => handleFeedback('positive')}
                          className="h-6 w-6 p-0 bg-transparent hover:bg-accent rounded"
                        >
                          <ThumbsUp className="h-3 w-3" />
                        </button>
                      </TooltipTrigger>
                      <TooltipContent>Good response</TooltipContent>
                    </Tooltip>

                    <Tooltip>
                      <TooltipTrigger asChild>
                        <button
                          onClick={() => handleFeedback('negative')}
                          className="h-6 w-6 p-0 bg-transparent hover:bg-accent rounded"
                        >
                          <ThumbsDown className="h-3 w-3" />
                        </button>
                      </TooltipTrigger>
                      <TooltipContent>Poor response</TooltipContent>
                    </Tooltip>
                  </>
                )}

                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button
                      className="h-6 w-6 p-0 bg-transparent hover:bg-accent rounded"
                    >
                      <MoreVertical className="h-3 w-3" />
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent>
                    {isUser && onEdit && (
                      <DropdownMenuItem onClick={() => setIsEditing(true)}>
                        <Edit3 className="h-4 w-4 mr-2" />
                        Edit
                      </DropdownMenuItem>
                    )}
                    {!isUser && onRegenerate && (
                      <DropdownMenuItem onClick={() => onRegenerate(message.id)}>
                        <RotateCcw className="h-4 w-4 mr-2" />
                        Regenerate
                      </DropdownMenuItem>
                    )}
                    <DropdownMenuItem onClick={handleCopy}>
                      <Copy className="h-4 w-4 mr-2" />
                      Copy
                    </DropdownMenuItem>
                    <DropdownMenuItem>
                      <Share className="h-4 w-4 mr-2" />
                      Share
                    </DropdownMenuItem>
                    <DropdownMenuItem>
                      <Download className="h-4 w-4 mr-2" />
                      Download
                    </DropdownMenuItem>
                    {onDelete && (
                      <DropdownMenuItem
                        onClick={() => onDelete(message.id)}
                        className="text-destructive"
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete
                      </DropdownMenuItem>
                    )}
                  </DropdownMenuContent>
                </DropdownMenu>
              </TooltipProvider>
            </div>
          )}
        </div>

        {/* Message Metadata */}
        <div className={cn(
          'flex items-center gap-2 text-xs text-muted-foreground',
          isUser ? 'flex-row-reverse' : 'flex-row'
        )}>
          {showTimestamp && (
            <span>{formatMessageTime(message.timestamp)}</span>
          )}

          {message.metadata?.tokens && (
            <span>{message.metadata.tokens} tokens</span>
          )}

          {message.metadata?.processingTime && (
            <span>{message.metadata.processingTime}ms</span>
          )}

          {status === 'success' && (
            <CheckCircle className="h-3 w-3 text-green-500" />
          )}

          {status === 'error' && (
            <AlertCircle className="h-3 w-3 text-destructive" />
          )}
        </div>

        {/* Attachments */}
        {message.attachments && message.attachments.length > 0 && (
          <div className={cn(
            'flex flex-wrap gap-2',
            isUser ? 'justify-end' : 'justify-start'
          )}>
            {message.attachments.map((attachment, index) => (
              <div
                key={index}
                className="flex items-center gap-2 bg-muted rounded-lg px-3 py-2 text-sm"
              >
                <span className="truncate max-w-[200px]">
                  {attachment.name || 'Attachment'}
                </span>
                <Badge className="text-xs">
                  {attachment.type || 'file'}
                </Badge>
              </div>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  )
}