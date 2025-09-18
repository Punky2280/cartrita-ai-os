/**
 * ConversationList Component - Cartrita AI OS v2
 *
 * Displays list of conversations with search and filtering
 */

import React, { useState, useMemo } from 'react';
import { cn } from '@/lib/utils';
import {
  SearchIcon,
  MessageSquareIcon,
  BrainCircuitIcon,
  ClockIcon,
  TrashIcon,
  StarIcon
} from 'lucide-react';
import { FadeInUp } from '../ui/FadeInUp';

interface Conversation {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: string;
  agentCount?: number;
  messageCount: number;
  isStarred?: boolean;
  participants?: Array<{
    id: string;
    name: string;
    color: string;
  }>;
}

interface ConversationListProps {
  conversations: Conversation[];
  currentConversationId?: string;
  onConversationSelect?: (conversationId: string) => void;
  onConversationDelete?: (conversationId: string) => void;
  onConversationStar?: (conversationId: string) => void;
  className?: string;
  showSearch?: boolean;
  maxHeight?: string;
}

export function ConversationList({
  conversations,
  currentConversationId,
  onConversationSelect,
  onConversationDelete,
  onConversationStar,
  className,
  showSearch = true,
  maxHeight = 'max-h-96'
}: ConversationListProps) {
  const [searchQuery, setSearchQuery] = useState('');

  // Filter conversations based on search
  const filteredConversations = useMemo(() => {
    if (!searchQuery.trim()) return conversations;

    return conversations.filter(conversation =>
      conversation.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      conversation.lastMessage.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [conversations, searchQuery]);

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${Math.floor(diffInHours)}h ago`;
    if (diffInHours < 24 * 7) return `${Math.floor(diffInHours / 24)}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className={cn('space-y-4', className)}>
      {/* Search */}
      {showSearch && (
        <div className="relative">
          <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-200 placeholder-gray-400 focus:outline-none focus:border-copilot-blue/50 transition-colors"
          />
        </div>
      )}

      {/* Conversations */}
      <div className={cn('space-y-2 overflow-y-auto scrollbar-thin scrollbar-track-transparent scrollbar-thumb-gray-600', maxHeight)}>
        {filteredConversations.length === 0 ? (
          <div className="text-center py-8">
            <MessageSquareIcon className="w-8 h-8 text-gray-600 mx-auto mb-2" />
            <p className="text-gray-400">
              {searchQuery ? 'No conversations found' : 'No conversations yet'}
            </p>
          </div>
        ) : (
          filteredConversations.map((conversation, index) => (
            <FadeInUp
              key={conversation.id}
              delay={index * 50}
            >
              <div
                className={cn(
                  'group relative p-4 rounded-lg border transition-all duration-200 cursor-pointer',
                  currentConversationId === conversation.id
                    ? 'bg-copilot-blue/10 border-copilot-blue/30'
                    : 'bg-gray-800 border-gray-700 hover:bg-gray-700 hover:border-gray-600'
                )}
                onClick={() => onConversationSelect?.(conversation.id)}
              >
                {/* Header */}
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div className="flex items-start gap-3 flex-1 min-w-0">
                    <MessageSquareIcon className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" />

                    <div className="min-w-0 flex-1">
                      <h3 className="text-sm font-medium text-gray-200 truncate">
                        {conversation.title}
                      </h3>

                      {/* Participants */}
                      {conversation.participants && conversation.participants.length > 0 && (
                        <div className="flex items-center gap-1 mt-1">
                          {conversation.participants.slice(0, 3).map(participant => (
                            <div
                              key={participant.id}
                              className="w-4 h-4 rounded-full flex-shrink-0"
                              style={{ backgroundColor: participant.color }}
                              title={participant.name}
                            />
                          ))}
                          {conversation.participants.length > 3 && (
                            <span className="text-xs text-gray-500 ml-1">
                              +{conversation.participants.length - 3}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    {/* Star */}
                    {onConversationStar && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onConversationStar(conversation.id);
                        }}
                        className={cn(
                          'p-1 rounded transition-colors',
                          conversation.isStarred
                            ? 'text-yellow-400 hover:text-yellow-300'
                            : 'text-gray-400 hover:text-yellow-400'
                        )}
                      >
                        <StarIcon className="w-4 h-4" fill={conversation.isStarred ? 'currentColor' : 'none'} />
                      </button>
                    )}

                    {/* Delete */}
                    {onConversationDelete && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onConversationDelete(conversation.id);
                        }}
                        className="p-1 text-gray-400 hover:text-red-400 rounded transition-colors"
                      >
                        <TrashIcon className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>

                {/* Last Message */}
                <p className="text-xs text-gray-400 mb-3 line-clamp-2 pl-8">
                  {conversation.lastMessage}
                </p>

                {/* Footer */}
                <div className="flex items-center justify-between text-xs text-gray-500 pl-8">
                  <div className="flex items-center gap-3">
                    {/* Timestamp */}
                    <div className="flex items-center gap-1">
                      <ClockIcon className="w-3 h-3" />
                      {formatTimestamp(conversation.timestamp)}
                    </div>

                    {/* Message Count */}
                    <div className="flex items-center gap-1">
                      <MessageSquareIcon className="w-3 h-3" />
                      {conversation.messageCount}
                    </div>
                  </div>

                  {/* Agent Count */}
                  {conversation.agentCount && (
                    <div className="flex items-center gap-1">
                      <BrainCircuitIcon className="w-3 h-3" />
                      {conversation.agentCount} agents
                    </div>
                  )}
                </div>
              </div>
            </FadeInUp>
          ))
        )}
      </div>
    </div>
  );
}

export default ConversationList;
