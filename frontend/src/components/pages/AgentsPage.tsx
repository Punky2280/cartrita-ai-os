/**
 * Agents Page - Cartrita AI OS v2
 *
 * Agent management interface with orchestration controls
 */

'use client';

import React from 'react';
import { useAtom } from 'jotai';
import { AgentOrchestrator } from '@/components/agents/AgentOrchestrator';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { FadeInUp } from '@/components/ui/FadeInUp';
import {
  agentsAtom,
  selectedAgentAtom,
  updateAgentStatusAtom
} from '@/lib/store/atoms';
import { useAgents, useAgentActions } from '@/lib/hooks/queries';
import { BrainCircuitIcon, PlusIcon, SettingsIcon } from 'lucide-react';

export default function AgentsPage() {
  const [agents] = useAtom(agentsAtom);
  const [selectedAgent, setSelectedAgent] = useAtom(selectedAgentAtom);
  const [, updateAgentStatus] = useAtom(updateAgentStatusAtom);

  // Query hooks
  const { data: serverAgents, isLoading, error, refetch } = useAgents();
  const { startAgent, pauseAgent, updateStatus, isLoading: isUpdating } = useAgentActions();

  // Use server data if available, fallback to local state
  const displayAgents = serverAgents || agents;

  // Handler functions
  const handleAgentSelect = (agent: any) => {
    setSelectedAgent(agent);
  };

  const handleAgentStart = async (agentId: string) => {
    try {
      await startAgent(agentId);
      updateAgentStatus({ agentId, status: 'active' });
    } catch (error) {
      console.error('Failed to start agent:', error);
    }
  };

  const handleAgentPause = async (agentId: string) => {
    try {
      await pauseAgent(agentId);
      updateAgentStatus({ agentId, status: 'idle' });
    } catch (error) {
      console.error('Failed to pause agent:', error);
    }
  };

  const handleAgentConfigure = (agentId: string) => {
    // TODO: Open agent configuration modal
    console.log('Configure agent:', agentId);
  };

  const handleAgentAdd = () => {
    // TODO: Open add agent modal
    console.log('Add new agent');
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <LoadingSpinner size="lg" message="Loading agents..." />
      </div>
    );
  }

  // Error state
  if (error && !displayAgents?.length) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center max-w-md">
          <BrainCircuitIcon className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <h2 className="text-lg font-semibold text-gray-100 mb-2">
            Unable to load agents
          </h2>
          <p className="text-gray-400 mb-4">
            {error instanceof Error ? error.message : 'Something went wrong'}
          </p>
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-copilot-blue hover:bg-copilot-blue/80 text-white rounded-lg transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <div className="flex-1 flex flex-col h-full bg-gray-950">
        {/* Header */}
        <div className="flex-shrink-0 px-6 py-6 border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-100 mb-2">
                AI Agents
              </h1>
              <p className="text-gray-400">
                Manage and orchestrate your AI agent workforce
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => refetch()}
                disabled={isLoading}
                className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-200 rounded-lg transition-colors disabled:opacity-50"
              >
                <SettingsIcon className="w-4 h-4" />
                Refresh
              </button>

              <button
                onClick={handleAgentAdd}
                className="flex items-center gap-2 px-4 py-2 bg-copilot-blue hover:bg-copilot-blue/80 text-white rounded-lg transition-colors"
              >
                <PlusIcon className="w-4 h-4" />
                Add Agent
              </button>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {!displayAgents?.length ? (
            // Empty state
            <div className="flex-1 flex items-center justify-center p-8">
              <div className="text-center max-w-md">
                <BrainCircuitIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                <h2 className="text-xl font-semibold text-gray-100 mb-2">
                  No agents configured
                </h2>
                <p className="text-gray-400 mb-6">
                  Get started by adding your first AI agent. Agents can help with coding,
                  research, creative tasks, and more.
                </p>
                <button
                  onClick={handleAgentAdd}
                  className="flex items-center gap-2 px-6 py-3 bg-copilot-blue hover:bg-copilot-blue/80 text-white rounded-lg transition-colors mx-auto"
                >
                  <PlusIcon className="w-5 h-5" />
                  Add Your First Agent
                </button>
              </div>
            </div>
          ) : (
            // Agents orchestrator
            <div className="p-6">
              <FadeInUp>
                <AgentOrchestrator
                  agents={displayAgents}
                  selectedAgent={selectedAgent || undefined}
                  onAgentSelect={handleAgentSelect}
                  onAgentStart={handleAgentStart}
                  onAgentPause={handleAgentPause}
                  onAgentConfigure={handleAgentConfigure}
                  onAgentAdd={handleAgentAdd}
                  showMetrics={true}
                />
              </FadeInUp>
            </div>
          )}
        </div>

        {/* Loading overlay for updates */}
        {isUpdating && (
          <div className="absolute inset-0 bg-black/20 backdrop-blur-sm flex items-center justify-center z-50">
            <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 flex items-center gap-3">
              <LoadingSpinner size="sm" />
              <span className="text-gray-200">Updating agents...</span>
            </div>
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
}
