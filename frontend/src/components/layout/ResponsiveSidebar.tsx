/**
 * ResponsiveSidebar Component - Cartrita AI OS v2
 *
 * Collapsible sidebar with navigation and agent overview
 */

import React, { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import {
  ChevronLeftIcon,
  ChevronRightIcon,
  MessageSquareIcon,
  BrainCircuitIcon,
  SettingsIcon,
  HistoryIcon,
  PlusIcon,
  MenuIcon,
  XIcon
} from 'lucide-react';

interface SidebarAgent {
  id: string;
  name: string;
  status: 'active' | 'idle' | 'busy' | 'error' | 'offline';
  color: string;
}

interface SidebarConversation {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: string;
  agentCount?: number;
}

interface ResponsiveSidebarProps {
  isCollapsed?: boolean;
  onCollapsedChange?: (collapsed: boolean) => void;
  agents?: SidebarAgent[];
  conversations?: SidebarConversation[];
  currentConversationId?: string;
  onConversationSelect?: (conversationId: string) => void;
  onNewConversation?: () => void;
  onAgentsView?: () => void;
  onSettingsView?: () => void;
  className?: string;
}

const navigationItems = [
  {
    id: 'chat',
    label: 'Chat',
    icon: MessageSquareIcon,
    path: '/chat'
  },
  {
    id: 'agents',
    label: 'Agents',
    icon: BrainCircuitIcon,
    path: '/agents'
  },
  {
    id: 'history',
    label: 'History',
    icon: HistoryIcon,
    path: '/history'
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: SettingsIcon,
    path: '/settings'
  }
];

export function ResponsiveSidebar({
  isCollapsed = false,
  onCollapsedChange,
  agents = [],
  conversations = [],
  currentConversationId,
  onConversationSelect,
  onNewConversation,
  onAgentsView,
  onSettingsView,
  className
}: ResponsiveSidebarProps) {
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [activeNav, setActiveNav] = useState('chat');
  const [isClient, setIsClient] = useState(false);

  // Hydration-safe client detection
  useEffect(() => {
    setIsClient(true);
  }, []);

  // Close mobile sidebar on resize
  useEffect(() => {
    if (!isClient) return;

    const handleResize = () => {
      if (window.innerWidth >= 768) {
        setIsMobileOpen(false);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [isClient]);

  const toggleCollapsed = () => {
    onCollapsedChange?.(!isCollapsed);
  };

  const toggleMobile = () => {
    setIsMobileOpen(!isMobileOpen);
  };

  const handleNavClick = (navId: string) => {
    setActiveNav(navId);

    switch (navId) {
      case 'agents':
        onAgentsView?.();
        break;
      case 'settings':
        onSettingsView?.();
        break;
    }

    // Close mobile menu (only on client)
    if (isClient && window.innerWidth < 768) {
      setIsMobileOpen(false);
    }
  };

  const sidebarContent = (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between">
          {!isCollapsed && (
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-r from-copilot-blue to-copilot-pink rounded-lg flex items-center justify-center">
                <BrainCircuitIcon className="w-5 h-5 text-white" />
              </div>
              <span className="text-lg font-semibold text-gray-100">
                Cartrita
              </span>
            </div>
          )}

          {/* Desktop collapse button */}
          <button
            onClick={toggleCollapsed}
            className="hidden md:block p-1 text-gray-400 hover:text-gray-200 hover:bg-gray-700 rounded transition-colors"
          >
            {isCollapsed ? (
              <ChevronRightIcon className="w-5 h-5" />
            ) : (
              <ChevronLeftIcon className="w-5 h-5" />
            )}
          </button>

          {/* Mobile close button */}
          <button
            onClick={toggleMobile}
            className="md:hidden p-1 text-gray-400 hover:text-gray-200 hover:bg-gray-700 rounded transition-colors"
          >
            <XIcon className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Navigation */}
      <div className="p-4 border-b border-gray-700">
        <nav className="space-y-2">
          {navigationItems.map(item => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => handleNavClick(item.id)}
                className={cn(
                  'w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors text-left',
                  activeNav === item.id
                    ? 'bg-copilot-blue/10 text-copilot-blue border border-copilot-blue/30'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700'
                )}
              >
                <Icon className="w-5 h-5 flex-shrink-0" />
                {!isCollapsed && (
                  <span className="text-sm font-medium">
                    {item.label}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* New Conversation */}
      {!isCollapsed && (
        <div className="p-4 border-b border-gray-700">
          <button
            onClick={onNewConversation}
            className="w-full flex items-center gap-2 px-3 py-2 bg-copilot-blue hover:bg-copilot-blue/80 text-white rounded-lg transition-colors text-sm font-medium"
          >
            <PlusIcon className="w-4 h-4" />
            New Conversation
          </button>
        </div>
      )}

      {/* Conversations List */}
      {!isCollapsed && conversations.length > 0 && (
        <div className="flex-1 overflow-hidden">
          <div className="p-4 pb-2">
            <h3 className="text-sm font-medium text-gray-400 mb-2">
              Recent Conversations
            </h3>
          </div>

          <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-2 scrollbar-thin scrollbar-track-transparent scrollbar-thumb-gray-600">
            {conversations.map(conversation => (
              <button
                key={conversation.id}
                onClick={() => onConversationSelect?.(conversation.id)}
                className={cn(
                  'w-full text-left p-3 rounded-lg transition-colors border',
                  currentConversationId === conversation.id
                    ? 'bg-copilot-blue/10 border-copilot-blue/30'
                    : 'border-transparent hover:bg-gray-800 hover:border-gray-600'
                )}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-gray-200 truncate">
                      {conversation.title}
                    </p>
                    <p className="text-xs text-gray-400 truncate mt-1">
                      {conversation.lastMessage}
                    </p>
                  </div>
                  {conversation.agentCount && (
                    <span className="text-xs text-gray-400 bg-gray-700 px-2 py-1 rounded-full flex-shrink-0">
                      {conversation.agentCount}
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  {conversation.timestamp}
                </p>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Agent Status Summary */}
      {!isCollapsed && agents.length > 0 && (
        <div className="p-4 border-t border-gray-700">
          <h3 className="text-sm font-medium text-gray-400 mb-3">
            Active Agents
          </h3>
          <div className="space-y-2">
            {agents.slice(0, 3).map(agent => (
              <div key={agent.id} className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full flex-shrink-0"
                  style={{ backgroundColor: agent.color }}
                />
                <span className="text-sm text-gray-300 truncate flex-1">
                  {agent.name}
                </span>
                <div className={cn(
                  'w-2 h-2 rounded-full flex-shrink-0',
                  agent.status === 'active' && 'bg-green-400',
                  agent.status === 'busy' && 'bg-yellow-400',
                  agent.status === 'idle' && 'bg-gray-400',
                  agent.status === 'error' && 'bg-red-400',
                  agent.status === 'offline' && 'bg-gray-600'
                )} />
              </div>
            ))}
            {agents.length > 3 && (
              <p className="text-xs text-gray-500 mt-2">
                +{agents.length - 3} more agents
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={toggleMobile}
        className="md:hidden fixed top-4 left-4 z-50 p-2 bg-gray-800 border border-gray-600 text-gray-300 rounded-lg hover:bg-gray-700 transition-colors"
      >
        <MenuIcon className="w-5 h-5" />
      </button>

      {/* Mobile Overlay */}
      {isMobileOpen && (
        <div
          className="md:hidden fixed inset-0 z-40 bg-black/50"
          onClick={toggleMobile}
        />
      )}

      {/* Desktop Sidebar */}
      <div
        className={cn(
          'hidden md:flex flex-col bg-gray-900 border-r border-gray-700 transition-all duration-200',
          isCollapsed ? 'w-16' : 'w-80',
          className
        )}
      >
        {sidebarContent}
      </div>

      {/* Mobile Sidebar */}
      <div
        className={cn(
          'md:hidden fixed inset-y-0 left-0 z-50 w-80 bg-gray-900 border-r border-gray-700 transform transition-transform',
          isMobileOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {sidebarContent}
      </div>
    </>
  );
}

export default ResponsiveSidebar;
