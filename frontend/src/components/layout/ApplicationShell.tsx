/**
 * ApplicationShell Component - Cartrita AI OS v2
 *
 * Main layout container with responsive three-column design
 */

import React, { useState, ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { ResponsiveSidebar } from './ResponsiveSidebar';

interface ApplicationShellProps {
  children: ReactNode;
  sidebar?: {
    agents?: Array<{
      id: string;
      name: string;
      status: 'active' | 'idle' | 'busy' | 'error' | 'offline';
      color: string;
    }>;
    conversations?: Array<{
      id: string;
      title: string;
      lastMessage: string;
      timestamp: string;
      agentCount?: number;
    }>;
    currentConversationId?: string;
    onConversationSelect?: (conversationId: string) => void;
    onNewConversation?: () => void;
    onAgentsView?: () => void;
    onSettingsView?: () => void;
  };
  rightPanel?: {
    isOpen?: boolean;
    onToggle?: () => void;
    content?: ReactNode;
    title?: string;
  };
  className?: string;
  suppressHydrationWarning?: boolean;
}

export function ApplicationShell({
  children,
  sidebar,
  rightPanel,
  className,
  suppressHydrationWarning = false
}: ApplicationShellProps) {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  return (
    <div
      className={cn('min-h-screen bg-gray-950 text-gray-100', className)}
      suppressHydrationWarning={suppressHydrationWarning}
    >
      {/* Main Container */}
      <div className="flex h-screen overflow-hidden">
        {/* Left Sidebar */}
        <ResponsiveSidebar
          isCollapsed={isSidebarCollapsed}
          onCollapsedChange={setIsSidebarCollapsed}
          agents={sidebar?.agents}
          conversations={sidebar?.conversations}
          currentConversationId={sidebar?.currentConversationId}
          onConversationSelect={sidebar?.onConversationSelect}
          onNewConversation={sidebar?.onNewConversation}
          onAgentsView={sidebar?.onAgentsView}
          onSettingsView={sidebar?.onSettingsView}
        />

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Content */}
          <main className="flex-1 overflow-hidden bg-gray-950">
            {children}
          </main>
        </div>

        {/* Right Panel */}
        {rightPanel?.isOpen && (
          <div className="hidden lg:flex w-80 bg-gray-900 border-l border-gray-700 flex-col">
            {/* Panel Header */}
            {rightPanel.title && (
              <div className="p-4 border-b border-gray-700">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-gray-100">
                    {rightPanel.title}
                  </h2>
                  {rightPanel.onToggle && (
                    <button
                      onClick={rightPanel.onToggle}
                      className="p-1 text-gray-400 hover:text-gray-200 hover:bg-gray-700 rounded transition-colors"
                    >
                      ×
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Panel Content */}
            <div className="flex-1 overflow-y-auto">
              {rightPanel.content}
            </div>
          </div>
        )}
      </div>

      {/* Mobile Right Panel Overlay */}
      {rightPanel?.isOpen && (
        <>
          {/* Overlay */}
          <div
            className="lg:hidden fixed inset-0 z-40 bg-black/50"
            onClick={rightPanel.onToggle}
          />

          {/* Panel */}
          <div className="lg:hidden fixed inset-y-0 right-0 z-50 w-80 bg-gray-900 border-l border-gray-700 transform transition-transform translate-x-0">
            {/* Panel Header */}
            {rightPanel.title && (
              <div className="p-4 border-b border-gray-700">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-gray-100">
                    {rightPanel.title}
                  </h2>
                  {rightPanel.onToggle && (
                    <button
                      onClick={rightPanel.onToggle}
                      className="p-1 text-gray-400 hover:text-gray-200 hover:bg-gray-700 rounded transition-colors"
                    >
                      ×
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Panel Content */}
            <div className="flex-1 overflow-y-auto p-4">
              {rightPanel.content}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default ApplicationShell;
