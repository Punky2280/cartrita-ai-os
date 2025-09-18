/**
 * Main App Component - Cartrita AI OS v2
 *
 * Root application with routing and state providers
 */

'use client';

import React, { useState } from 'react';
import { useAtom } from 'jotai';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ClientOnly } from '@/components/ClientOnly';
import { ApplicationShell } from '@/components/layout/ApplicationShell';
import ChatPage from '@/components/pages/ChatPage';
import AgentsPage from '@/components/pages/AgentsPage';
import SettingsPage from '@/components/pages/SettingsPage';
import { ConversationList } from '@/components/conversations/ConversationList';
import {
  conversationsAtom,
  currentConversationIdAtom,
  agentsAtom,
  createConversationAtom,
  uiStateAtom
} from '@/lib/store/atoms';

// Create a client instance
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      refetchOnWindowFocus: false,
    },
  },
});

function AppContent() {
  const [conversations] = useAtom(conversationsAtom);
  const [currentConversationId, setCurrentConversationId] = useAtom(currentConversationIdAtom);
  const [agents] = useAtom(agentsAtom);
  const [uiState, setUiState] = useAtom(uiStateAtom);
  const [, createConversation] = useAtom(createConversationAtom);

  // Handle navigation
  const handleViewChange = (view: 'chat' | 'agents' | 'settings' | 'history') => {
    setUiState(prev => ({ ...prev, currentView: view }));
  };

  // Handle conversation actions
  const handleConversationSelect = (conversationId: string) => {
    setCurrentConversationId(conversationId);
    setUiState(prev => ({ ...prev, currentView: 'chat' }));
  };

  const handleNewConversation = () => {
    const conversationId = createConversation({
      title: `New Conversation ${new Date().toLocaleString()}`,
      agents: agents.filter(a => a.status === 'active').slice(0, 2),
    });
    setUiState(prev => ({ ...prev, currentView: 'chat' }));
  };

  // Handle right panel
  const handleRightPanelToggle = () => {
    setUiState(prev => ({
      ...prev,
      rightPanelOpen: !prev.rightPanelOpen,
    }));
  };

  // Prepare sidebar data
  const sidebarAgents = agents.map(agent => ({
    id: agent.id,
    name: agent.name,
    status: agent.status,
    color: agent.color,
  }));

      const sidebarConversations = conversations.map(conv => ({
      id: conv.id,
      title: conv.title,
      lastMessage: conv.messages[conv.messages.length - 1]?.content || 'No messages',
      timestamp: conv.updatedAt,
      agentCount: conv.participants.length,
      messageCount: conv.messages.length,
    }));

  // Right panel content based on current view
  const getRightPanelContent = () => {
    if (uiState.currentView === 'chat' && conversations.length > 0) {
      return (
        <ConversationList
          conversations={sidebarConversations}
          currentConversationId={currentConversationId || undefined}
          onConversationSelect={handleConversationSelect}
          onConversationDelete={(id) => {
            // TODO: Implement conversation deletion
            console.log('Delete conversation:', id);
          }}
          onConversationStar={(id) => {
            // TODO: Implement conversation starring
            console.log('Star conversation:', id);
          }}
          showSearch={true}
          maxHeight="max-h-full"
        />
      );
    }
    return null;
  };

  // Render current view
  const renderCurrentView = () => {
    switch (uiState.currentView) {
      case 'agents':
        return <AgentsPage />;
      case 'settings':
        return <SettingsPage />;
      case 'chat':
      default:
        return <ChatPage conversationId={currentConversationId || undefined} />;
    }
  };

  return (
    <ApplicationShell
      sidebar={{
        agents: sidebarAgents,
        conversations: sidebarConversations,
        currentConversationId: currentConversationId || undefined,
        onConversationSelect: handleConversationSelect,
        onNewConversation: handleNewConversation,
        onAgentsView: () => handleViewChange('agents'),
        onSettingsView: () => handleViewChange('settings'),
      }}
      rightPanel={{
        isOpen: uiState.rightPanelOpen && uiState.currentView === 'chat',
        onToggle: handleRightPanelToggle,
        content: getRightPanelContent(),
        title: 'Conversations',
      }}
      suppressHydrationWarning
    >
      {renderCurrentView()}
    </ApplicationShell>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ClientOnly
        fallback={
          <div className="min-h-screen bg-gray-950 flex items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-copilot-blue"></div>
          </div>
        }
      >
        <AppContent />
      </ClientOnly>
    </QueryClientProvider>
  );
}
