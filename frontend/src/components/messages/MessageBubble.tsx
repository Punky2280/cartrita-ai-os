/**
 * MessageBubble Component - Cartrita AI OS v2
 *
 * A comprehensive message bubble component supporting all message types
 * with proper styling, streaming states, and accessibility features.
 */

import React from 'react';
import { cn } from '@/lib/utils';
import { MessageBubbleProps, MessageRole } from '@/types';
import { FadeInUp } from '@/components/ui/FadeInUp';

// Styling configurations based on message role
const bubbleStyles: Record<MessageRole, string> = {
  user: 'bubble-user max-w-[80%] ml-auto rounded-br-sm',
  assistant: 'bubble-assistant max-w-[85%] mr-auto rounded-bl-sm',
  system: 'bubble-system max-w-[90%] mx-auto rounded-md text-center',
  agent: 'bubble-agent max-w-[85%] mr-auto rounded-bl-sm',
};

const avatarStyles: Record<MessageRole, string> = {
  user: 'bg-gradient-to-r from-copilot-blue to-copilot-pink text-white',
  assistant: 'bg-gray-700 text-gray-200',
  system: 'bg-gray-600 text-gray-300',
  agent: 'bg-gradient-to-r from-anthropic-orange to-yellow-600 text-white',
};

export function MessageBubble({
  message,
  variant = message.role,
  isStreaming = false,
  showTimestamp = true,
  showActions = true,
  onEdit,
  onDelete,
  onReact,
  className,
}: MessageBubbleProps) {
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / (1000 * 60));

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (minutes < 1440) return `${Math.floor(minutes / 60)}h ago`;
    return date.toLocaleDateString();
  };

  const getInitials = (role: MessageRole): string => {
    switch (role) {
      case 'user': return 'U';
      case 'assistant': return 'AI';
      case 'system': return 'SYS';
      case 'agent': return 'AG';
      default: return 'AI';
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent, action: () => void) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      action();
    }
  };

  return (
    <FadeInUp delay={0.1} className={cn('group relative', className)}>
      <div className={cn(
        'flex items-start gap-3 p-4 rounded-lg transition-all duration-200',
        variant !== 'user' && 'hover:bg-gray-800/30',
        className
      )}>
        {/* Avatar */}
        {variant !== 'system' && (
          <div className={cn(
            'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold',
            avatarStyles[variant]
          )}>
            {getInitials(variant)}
          </div>
        )}

        {/* Message Content */}
        <div className={cn(
          'flex-1 min-w-0 px-4 py-3 rounded-lg relative',
          bubbleStyles[variant],
          isStreaming && 'animate-pulse'
        )}>
          {/* Message Text */}
          <div className="prose prose-sm max-w-none">
            <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
              {message.content}
            </p>
          </div>

          {/* Streaming Indicator */}
          {isStreaming && (
            <div className="flex items-center gap-1 mt-2">
              <div className="flex space-x-1">
                <div className="w-1.5 h-1.5 bg-current rounded-full animate-bounce-dots" />
                <div className="w-1.5 h-1.5 bg-current rounded-full animate-bounce-dots" style={{ animationDelay: '0.1s' }} />
                <div className="w-1.5 h-1.5 bg-current rounded-full animate-bounce-dots" style={{ animationDelay: '0.2s' }} />
              </div>
              <span className="text-xs opacity-70 ml-2">AI is thinking...</span>
            </div>
          )}

          {/* Attachments */}
          {message.attachments && message.attachments.length > 0 && (
            <div className="mt-3 space-y-2">
              {message.attachments.map((attachment) => (
                <div
                  key={attachment.id}
                  className="flex items-center gap-2 p-2 bg-gray-700/50 rounded border border-gray-600"
                >
                  <div className="w-4 h-4 bg-gray-500 rounded flex-shrink-0" />
                  <span className="text-xs text-gray-300 truncate">
                    {attachment.name}
                  </span>
                  <span className="text-xs text-gray-500">
                    {(attachment.size / 1024).toFixed(1)}KB
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Metadata */}
          {message.metadata && (
            <div className="mt-2 flex items-center gap-2 text-xs text-gray-500">
              {message.metadata.model && (
                <span className="px-2 py-1 bg-gray-700 rounded text-gray-300">
                  {message.metadata.model}
                </span>
              )}
              {message.tokens && (
                <span>{message.tokens} tokens</span>
              )}
              {message.metadata.processingTime && (
                <span>{message.metadata.processingTime}ms</span>
              )}
            </div>
          )}
        </div>

        {/* Timestamp */}
        {showTimestamp && (
          <div className="flex-shrink-0 text-xs text-gray-500 mt-1">
            {formatTimestamp(message.timestamp)}
          </div>
        )}
      </div>

      {/* Message Actions */}
      {showActions && !isStreaming && (
        <div className="absolute right-4 top-4 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          <div className="flex items-center gap-1 bg-gray-800 border border-gray-700 rounded-lg px-2 py-1">
            {/* Copy Button */}
            <button
              className="p-1 hover:bg-gray-700 rounded text-gray-400 hover:text-gray-200 transition-colors"
              onClick={() => navigator.clipboard.writeText(message.content)}
              onKeyDown={(e) => handleKeyDown(e, () => navigator.clipboard.writeText(message.content))}
              aria-label="Copy message"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </button>

            {/* Edit Button */}
            {variant === 'user' && onEdit && (
              <button
                className="p-1 hover:bg-gray-700 rounded text-gray-400 hover:text-gray-200 transition-colors"
                onClick={() => onEdit(message.id, message.content)}
                onKeyDown={(e) => handleKeyDown(e, () => onEdit(message.id, message.content))}
                aria-label="Edit message"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </button>
            )}

            {/* React Button */}
            {onReact && (
              <button
                className="p-1 hover:bg-gray-700 rounded text-gray-400 hover:text-gray-200 transition-colors"
                onClick={() => onReact(message.id, '👍')}
                onKeyDown={(e) => handleKeyDown(e, () => onReact(message.id, '👍'))}
                aria-label="React to message"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
                </svg>
              </button>
            )}

            {/* Delete Button */}
            {onDelete && (
              <button
                className="p-1 hover:bg-red-600 rounded text-gray-400 hover:text-white transition-colors"
                onClick={() => onDelete(message.id)}
                onKeyDown={(e) => handleKeyDown(e, () => onDelete(message.id))}
                aria-label="Delete message"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            )}
          </div>
        </div>
      )}
    </FadeInUp>
  );
}

export default MessageBubble;
