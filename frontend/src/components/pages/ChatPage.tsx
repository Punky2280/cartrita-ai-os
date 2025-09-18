/**
 * Chat Page - Cartrita AI OS v2
 *
 * Main chat interface with message history and agent interaction
 */

'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useAtom } from 'jotai';
import { MessageBubble } from '@/components/messages/MessageBubble';
import { StreamingIndicator } from '@/components/messages/StreamingIndicator';
import { EnhancedMessageInput } from '@/components/messages/EnhancedMessageInput';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { FadeInUp } from '@/components/ui/FadeInUp';
import {
  currentConversationAtom,
  selectedAgentAtom,
  agentsAtom,
  addMessageAtom
} from '@/lib/store/atoms';
import { useConversation, useConversationActions } from '@/lib/hooks/queries';
import { useChatStreaming } from '@/lib/hooks/streaming';
import { cn } from '@/lib/utils';
import { BrainCircuitIcon, SparklesIcon } from 'lucide-react';

interface ChatPageProps {
  conversationId?: string;
}

export default function ChatPage({ conversationId }: ChatPageProps) {
  const [currentConversation] = useAtom(currentConversationAtom);
  const [selectedAgent] = useAtom(selectedAgentAtom);
  const [agents] = useAtom(agentsAtom);
  const [, addMessage] = useAtom(addMessageAtom);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [isComposing, setIsComposing] = useState(false);

  // Query hooks
  const { data: conversation, isLoading, error } = useConversation(
    conversationId || currentConversation?.id || ''
  );
  const { sendMessage, isLoading: isSending } = useConversationActions(
    conversationId || currentConversation?.id
  );

  // Streaming hook
  const {
    isStreaming,
    isConnected,
    error: streamingError,
    getStreamingMessage,
    isMessageStreaming,
  } = useChatStreaming(conversationId || currentConversation?.id || '');

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversation?.messages, isStreaming]);

  // Handle message send
  const handleSendMessage = async (
    message: string,
    attachments: any[] = [],
    selectedAgent?: any
  ) => {
    if (!message.trim()) return;

    try {
      await sendMessage(message, selectedAgent?.id, attachments);
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  // Convert agents to format expected by EnhancedMessageInput
  const compatibleAgents = agents?.filter(agent => {
    // Filter to only include agents with compatible types
    return ['coding', 'research', 'creative', 'analysis'].includes(agent.type);
  }).map(agent => ({
    id: agent.id,
    name: agent.name,
    type: agent.type as 'coding' | 'research' | 'creative' | 'analysis',
    avatar: agent.avatar,
    color: agent.color || '#6e81ff'
  }));

  const compatibleSelectedAgent = selectedAgent &&
    ['coding', 'research', 'creative', 'analysis'].includes(selectedAgent.type)
    ? {
        id: selectedAgent.id,
        name: selectedAgent.name,
        type: selectedAgent.type as 'coding' | 'research' | 'creative' | 'analysis',
        avatar: selectedAgent.avatar,
        color: selectedAgent.color || '#6e81ff'
      }
    : undefined;

  // Loading state
  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <LoadingSpinner size="lg" message="Loading conversation..." />
      </div>
    );
  }

  // Error state
  if (error && !conversation) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center">
          <BrainCircuitIcon className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <h2 className="text-lg font-semibold text-gray-100 mb-2">
            Unable to load conversation
          </h2>
          <p className="text-gray-400">
            {error instanceof Error ? error.message : 'Something went wrong'}
          </p>
        </div>
      </div>
    );
  }

  const messages = conversation?.messages || [];
  const hasMessages = messages.length > 0;

  return (
    <ErrorBoundary>
      <div className="flex-1 flex flex-col h-full bg-gray-950">
        {/* Header */}
        {conversation && (
          <div className="flex-shrink-0 px-6 py-4 border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-lg font-semibold text-gray-100">
                  {conversation.title}
                </h1>
                <div className="flex items-center gap-2 mt-1">
                  {conversation.participants?.map((agent) => (
                    <div key={agent.id} className="flex items-center gap-1 text-sm text-gray-400">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: agent.color }}
                      />
                      {agent.name}
                    </div>
                  ))}
                  {!isConnected && (
                    <span className="text-xs text-red-400 bg-red-400/10 px-2 py-1 rounded-full">
                      Disconnected
                    </span>
                  )}
                </div>
              </div>

              {selectedAgent && (
                <div className="flex items-center gap-2 px-3 py-2 bg-gray-800 rounded-lg border border-gray-700">
                  <div
                    className="w-4 h-4 rounded-full"
                    style={{ backgroundColor: selectedAgent.color }}
                  />
                  <span className="text-sm text-gray-200">{selectedAgent.name}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto">
          {!hasMessages ? (
            // Empty state
            <div className="flex-1 flex items-center justify-center p-8">
              <div className="text-center max-w-md">
                <SparklesIcon className="w-16 h-16 text-copilot-blue mx-auto mb-4" />
                <h2 className="text-xl font-semibold text-gray-100 mb-2">
                  Start a conversation
                </h2>
                <p className="text-gray-400 mb-6">
                  Ask questions, get help with coding, research topics, or have a creative discussion.
                  Your AI agents are ready to assist you.
                </p>
                <div className="grid grid-cols-1 gap-2 text-left">
                  <div className="p-3 bg-gray-800 rounded-lg border border-gray-700">
                    <p className="text-sm text-gray-200">💻 "Help me debug this JavaScript code"</p>
                  </div>
                  <div className="p-3 bg-gray-800 rounded-lg border border-gray-700">
                    <p className="text-sm text-gray-200">🔍 "Research the latest trends in AI"</p>
                  </div>
                  <div className="p-3 bg-gray-800 rounded-lg border border-gray-700">
                    <p className="text-sm text-gray-200">✨ "Write a creative story about robots"</p>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            // Messages list
            <div className="px-6 py-4 space-y-4">
              {messages.map((message, index) => {
                const streamingMessage = getStreamingMessage(message.id);
                const isCurrentlyStreaming = isMessageStreaming(message.id);

                return (
                  <FadeInUp key={message.id} delay={index * 100}>
                    <MessageBubble
                      message={{
                        ...message,
                        content: streamingMessage?.content || message.content,
                        conversationId: conversationId || currentConversation?.id || ''
                      }}
                      isStreaming={isCurrentlyStreaming}
                      onReact={(messageId, emoji) => {
                        // TODO: Implement reaction handling
                        console.log('React with:', emoji);
                      }}
                      onEdit={(messageId, newContent) => {
                        // TODO: Implement message editing
                        console.log('Edit message:', messageId, newContent);
                      }}
                      onDelete={(messageId) => {
                        // TODO: Implement message deletion
                        console.log('Delete message:', messageId);
                      }}
                    />
                  </FadeInUp>
                );
              })}

              {/* Streaming indicator */}
              {isStreaming && (
                <FadeInUp>
                  <StreamingIndicator />
                </FadeInUp>
              )}

              {/* Bottom spacer for auto-scroll */}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input */}
        <div className="flex-shrink-0 p-6 border-t border-gray-800 bg-gray-900/50 backdrop-blur-sm">
          <EnhancedMessageInput
            placeholder={
              selectedAgent
                ? `Message ${selectedAgent.name}...`
                : "Message Cartrita AI..."
            }
            onSubmit={handleSendMessage}
            disabled={isSending || isStreaming}
            isLoading={isSending}
            agents={compatibleAgents}
            selectedAgent={compatibleSelectedAgent}
            onAgentSelect={(agent) => {
              // TODO: Update selected agent
              console.log('Select agent:', agent);
            }}
            allowAttachments={true}
            allowVoiceInput={true}
            maxLength={4000}
          />

          {streamingError && (
            <div className="mt-2 p-2 bg-red-400/10 border border-red-400/30 rounded text-sm text-red-400">
              Connection issue: {streamingError}
            </div>
          )}
        </div>
      </div>
    </ErrorBoundary>
  );
}
