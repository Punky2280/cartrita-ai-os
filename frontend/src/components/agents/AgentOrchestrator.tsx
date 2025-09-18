/**
 * AgentOrchestrator Component - Cartrita AI OS v2
 *
 * Multi-agent management interface with task distribution and coordination
 */

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import {
  PlayIcon,
  PauseIcon,
  PlusIcon,
  FilterIcon,
  GridIcon,
  ListIcon,
  BarChart3Icon,
  SettingsIcon
} from 'lucide-react';
import { AgentCard } from './AgentCard';

interface Agent {
  id: string;
  name: string;
  type: 'coding' | 'research' | 'creative' | 'analysis' | 'orchestrator';
  status: 'active' | 'idle' | 'busy' | 'error' | 'offline';
  description: string;
  avatar?: string;
  color: string;
  capabilities?: Array<{
    id: string;
    name: string;
    description: string;
    enabled: boolean;
  }>;
  metrics?: {
    tasksCompleted: number;
    successRate: number;
    averageResponseTime: number;
    uptime: number;
  };
  currentTask?: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
}

interface AgentOrchestratorProps {
  agents: Agent[];
  selectedAgent?: Agent;
  onAgentSelect?: (agent: Agent) => void;
  onAgentStart?: (agentId: string) => void;
  onAgentPause?: (agentId: string) => void;
  onAgentConfigure?: (agentId: string) => void;
  onAgentAdd?: () => void;
  className?: string;
  showMetrics?: boolean;
}

type ViewMode = 'grid' | 'list';
type FilterType = 'all' | 'active' | 'idle' | 'busy' | 'error' | 'offline';
type SortType = 'name' | 'status' | 'priority' | 'tasks';

export function AgentOrchestrator({
  agents,
  selectedAgent,
  onAgentSelect,
  onAgentStart,
  onAgentPause,
  onAgentConfigure,
  onAgentAdd,
  className,
  showMetrics = false
}: AgentOrchestratorProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [filter, setFilter] = useState<FilterType>('all');
  const [sortBy, setSortBy] = useState<SortType>('name');
  const [showFilters, setShowFilters] = useState(false);

  // Filter and sort agents
  const filteredAndSortedAgents = agents
    .filter(agent => {
      if (filter === 'all') return true;
      return agent.status === filter;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'status':
          return a.status.localeCompare(b.status);
        case 'priority':
          const priorityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
          return priorityOrder[b.priority] - priorityOrder[a.priority];
        case 'tasks':
          return (b.metrics?.tasksCompleted || 0) - (a.metrics?.tasksCompleted || 0);
        default:
          return 0;
      }
    });

  // Get status counts
  const statusCounts = agents.reduce((acc, agent) => {
    acc[agent.status] = (acc[agent.status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const activeCount = statusCounts.active || 0;
  const totalCount = agents.length;

  const startAllAgents = () => {
    agents.forEach(agent => {
      if ((agent.status === 'idle' || agent.status === 'offline') && onAgentStart) {
        onAgentStart(agent.id);
      }
    });
  };

  const pauseAllAgents = () => {
    agents.forEach(agent => {
      if ((agent.status === 'active' || agent.status === 'busy') && onAgentPause) {
        onAgentPause(agent.id);
      }
    });
  };

  return (
    <div className={cn('space-y-4', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-100">
            Agent Orchestrator
          </h2>
          <p className="text-sm text-gray-400">
            {activeCount} of {totalCount} agents active
          </p>
        </div>

        {/* Global Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={startAllAgents}
            className="flex items-center gap-2 px-3 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg transition-colors"
          >
            <PlayIcon className="w-4 h-4" />
            Start All
          </button>

          <button
            onClick={pauseAllAgents}
            className="flex items-center gap-2 px-3 py-2 bg-yellow-600 hover:bg-yellow-700 text-white text-sm font-medium rounded-lg transition-colors"
          >
            <PauseIcon className="w-4 h-4" />
            Pause All
          </button>

          {onAgentAdd && (
            <button
              onClick={onAgentAdd}
              className="flex items-center gap-2 px-3 py-2 bg-copilot-blue hover:bg-copilot-blue/80 text-white text-sm font-medium rounded-lg transition-colors"
            >
              <PlusIcon className="w-4 h-4" />
              Add Agent
            </button>
          )}
        </div>
      </div>

      {/* Stats Overview */}
      {showMetrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Active Agents</p>
                <p className="text-2xl font-semibold text-green-400">
                  {statusCounts.active || 0}
                </p>
              </div>
              <BarChart3Icon className="w-8 h-8 text-green-400" />
            </div>
          </div>

          <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Busy Agents</p>
                <p className="text-2xl font-semibold text-copilot-blue">
                  {statusCounts.busy || 0}
                </p>
              </div>
              <BarChart3Icon className="w-8 h-8 text-copilot-blue" />
            </div>
          </div>

          <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Idle Agents</p>
                <p className="text-2xl font-semibold text-yellow-400">
                  {statusCounts.idle || 0}
                </p>
              </div>
              <BarChart3Icon className="w-8 h-8 text-yellow-400" />
            </div>
          </div>

          <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Total Tasks</p>
                <p className="text-2xl font-semibold text-gray-200">
                  {agents.reduce((sum, agent) => sum + (agent.metrics?.tasksCompleted || 0), 0)}
                </p>
              </div>
              <BarChart3Icon className="w-8 h-8 text-gray-400" />
            </div>
          </div>
        </div>
      )}

      {/* Controls */}
      <div className="flex items-center justify-between">
        {/* View Mode & Filters */}
        <div className="flex items-center gap-2">
          <div className="flex items-center bg-gray-800 border border-gray-700 rounded-lg p-1">
            <button
              onClick={() => setViewMode('grid')}
              className={cn(
                'p-2 rounded transition-colors',
                viewMode === 'grid'
                  ? 'bg-copilot-blue text-white'
                  : 'text-gray-400 hover:text-gray-200'
              )}
            >
              <GridIcon className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={cn(
                'p-2 rounded transition-colors',
                viewMode === 'list'
                  ? 'bg-copilot-blue text-white'
                  : 'text-gray-400 hover:text-gray-200'
              )}
            >
              <ListIcon className="w-4 h-4" />
            </button>
          </div>

          <button
            onClick={() => setShowFilters(!showFilters)}
            className={cn(
              'flex items-center gap-2 px-3 py-2 border rounded-lg transition-colors',
              showFilters
                ? 'bg-copilot-blue/10 border-copilot-blue/30 text-copilot-blue'
                : 'bg-gray-800 border-gray-700 text-gray-400 hover:text-gray-200'
            )}
          >
            <FilterIcon className="w-4 h-4" />
            Filters
          </button>
        </div>

        {/* Sort */}
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as SortType)}
          className="px-3 py-2 bg-gray-800 border border-gray-700 text-gray-200 rounded-lg focus:outline-none focus:border-copilot-blue/50"
        >
          <option value="name">Sort by Name</option>
          <option value="status">Sort by Status</option>
          <option value="priority">Sort by Priority</option>
          <option value="tasks">Sort by Tasks</option>
        </select>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
          <div className="flex flex-wrap gap-2">
            {(['all', 'active', 'idle', 'busy', 'error', 'offline'] as FilterType[]).map(status => (
              <button
                key={status}
                onClick={() => setFilter(status)}
                className={cn(
                  'px-3 py-2 text-sm font-medium rounded-lg transition-colors capitalize',
                  filter === status
                    ? 'bg-copilot-blue text-white'
                    : 'bg-gray-800 text-gray-400 hover:text-gray-200 hover:bg-gray-700'
                )}
              >
                {status} {status !== 'all' && `(${statusCounts[status] || 0})`}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Agents Grid/List */}
      {filteredAndSortedAgents.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-400">No agents match the current filter</p>
        </div>
      ) : (
        <div className={cn(
          viewMode === 'grid'
            ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'
            : 'space-y-3'
        )}>
          {filteredAndSortedAgents.map(agent => (
            <AgentCard
              key={agent.id}
              id={agent.id}
              name={agent.name}
              type={agent.type}
              status={agent.status}
              description={agent.description}
              avatar={agent.avatar}
              color={agent.color}
              capabilities={agent.capabilities}
              metrics={agent.metrics}
              currentTask={agent.currentTask}
              priority={agent.priority}
              onStart={() => onAgentStart?.(agent.id)}
              onPause={() => onAgentPause?.(agent.id)}
              onConfigure={() => onAgentConfigure?.(agent.id)}
              onSelect={() => onAgentSelect?.(agent)}
              isSelected={selectedAgent?.id === agent.id}
              showMetrics={showMetrics}
              size={viewMode === 'list' ? 'sm' : 'md'}
              className={viewMode === 'list' ? 'flex-row' : undefined}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default AgentOrchestrator;
