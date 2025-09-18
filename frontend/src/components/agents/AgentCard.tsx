/**
 * AgentCard Component - Cartrita AI OS v2
 *
 * Individual agent display with status, capabilities, and interaction
 */

import React from 'react';
import { cn } from '@/lib/utils';
import {
  PlayIcon,
  PauseIcon,
  SettingsIcon,
  TrendingUpIcon,
  ClockIcon,
  CheckCircleIcon,
  AlertCircleIcon,
  XCircleIcon
} from 'lucide-react';

interface AgentCapability {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
}

interface AgentMetrics {
  tasksCompleted: number;
  successRate: number;
  averageResponseTime: number;
  uptime: number;
}

interface AgentCardProps {
  id: string;
  name: string;
  type: 'coding' | 'research' | 'creative' | 'analysis' | 'orchestrator';
  status: 'active' | 'idle' | 'busy' | 'error' | 'offline';
  description: string;
  avatar?: string;
  color: string;
  capabilities?: AgentCapability[];
  metrics?: AgentMetrics;
  currentTask?: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  onStart?: () => void;
  onPause?: () => void;
  onConfigure?: () => void;
  onSelect?: () => void;
  isSelected?: boolean;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  showMetrics?: boolean;
}

const statusConfig = {
  active: {
    icon: CheckCircleIcon,
    color: 'text-green-400',
    bgColor: 'bg-green-400/10',
    borderColor: 'border-green-400/30',
    label: 'Active'
  },
  idle: {
    icon: ClockIcon,
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-400/10',
    borderColor: 'border-yellow-400/30',
    label: 'Idle'
  },
  busy: {
    icon: TrendingUpIcon,
    color: 'text-copilot-blue',
    bgColor: 'bg-copilot-blue/10',
    borderColor: 'border-copilot-blue/30',
    label: 'Busy'
  },
  error: {
    icon: AlertCircleIcon,
    color: 'text-red-400',
    bgColor: 'bg-red-400/10',
    borderColor: 'border-red-400/30',
    label: 'Error'
  },
  offline: {
    icon: XCircleIcon,
    color: 'text-gray-400',
    bgColor: 'bg-gray-400/10',
    borderColor: 'border-gray-400/30',
    label: 'Offline'
  }
};

const priorityColors = {
  low: 'border-l-gray-500',
  medium: 'border-l-yellow-400',
  high: 'border-l-orange-400',
  critical: 'border-l-red-400'
};

const sizeClasses = {
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-6'
};

export function AgentCard({
  id,
  name,
  type,
  status,
  description,
  avatar,
  color,
  capabilities = [],
  metrics,
  currentTask,
  priority,
  onStart,
  onPause,
  onConfigure,
  onSelect,
  isSelected = false,
  className,
  size = 'md',
  showMetrics = false
}: AgentCardProps) {
  const statusInfo = statusConfig[status];
  const StatusIcon = statusInfo.icon;

  const handleCardClick = () => {
    if (onSelect) {
      onSelect();
    }
  };

  const canStart = status === 'idle' || status === 'offline';
  const canPause = status === 'active' || status === 'busy';

  return (
    <div
      className={cn(
        'relative bg-gray-900 border border-gray-700 rounded-xl transition-all duration-200 hover:border-gray-600',
        `border-l-4 ${priorityColors[priority]}`,
        isSelected && 'border-copilot-blue/50 bg-copilot-blue/5',
        onSelect && 'cursor-pointer hover:bg-gray-800/50',
        sizeClasses[size],
        className
      )}
      onClick={handleCardClick}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          {/* Avatar */}
          <div
            className="w-10 h-10 rounded-full flex items-center justify-center text-white font-semibold text-sm"
            style={{ backgroundColor: color }}
          >
            {avatar || name.charAt(0).toUpperCase()}
          </div>

          {/* Name & Type */}
          <div>
            <h3 className="text-sm font-semibold text-gray-100">
              {name}
            </h3>
            <p className="text-xs text-gray-400 capitalize">
              {type} Agent
            </p>
          </div>
        </div>

        {/* Status */}
        <div className={cn(
          'flex items-center gap-2 px-2 py-1 rounded-full text-xs font-medium',
          statusInfo.bgColor,
          statusInfo.borderColor,
          'border'
        )}>
          <StatusIcon className={cn('w-3 h-3', statusInfo.color)} />
          <span className={statusInfo.color}>
            {statusInfo.label}
          </span>
        </div>
      </div>

      {/* Description */}
      <p className="text-sm text-gray-300 mb-3 line-clamp-2">
        {description}
      </p>

      {/* Current Task */}
      {currentTask && (
        <div className="mb-3 p-2 bg-gray-800/50 border border-gray-700 rounded-lg">
          <p className="text-xs text-gray-400 mb-1">Current Task:</p>
          <p className="text-sm text-gray-200 line-clamp-1">
            {currentTask}
          </p>
        </div>
      )}

      {/* Capabilities */}
      {capabilities.length > 0 && (
        <div className="mb-3">
          <p className="text-xs text-gray-400 mb-2">Capabilities:</p>
          <div className="flex flex-wrap gap-1">
            {capabilities.slice(0, 3).map(capability => (
              <span
                key={capability.id}
                className={cn(
                  'px-2 py-1 text-xs rounded-full',
                  capability.enabled
                    ? 'bg-green-400/10 text-green-400 border border-green-400/30'
                    : 'bg-gray-700 text-gray-400 border border-gray-600'
                )}
              >
                {capability.name}
              </span>
            ))}
            {capabilities.length > 3 && (
              <span className="px-2 py-1 text-xs rounded-full bg-gray-700 text-gray-400 border border-gray-600">
                +{capabilities.length - 3}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Metrics */}
      {showMetrics && metrics && (
        <div className="mb-3 grid grid-cols-2 gap-2 text-xs">
          <div className="bg-gray-800/50 p-2 rounded-lg">
            <p className="text-gray-400">Tasks</p>
            <p className="text-gray-200 font-semibold">{metrics.tasksCompleted}</p>
          </div>
          <div className="bg-gray-800/50 p-2 rounded-lg">
            <p className="text-gray-400">Success Rate</p>
            <p className="text-gray-200 font-semibold">{metrics.successRate}%</p>
          </div>
          <div className="bg-gray-800/50 p-2 rounded-lg">
            <p className="text-gray-400">Avg Response</p>
            <p className="text-gray-200 font-semibold">{metrics.averageResponseTime}ms</p>
          </div>
          <div className="bg-gray-800/50 p-2 rounded-lg">
            <p className="text-gray-400">Uptime</p>
            <p className="text-gray-200 font-semibold">{metrics.uptime}%</p>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {/* Start/Pause Button */}
          {canStart && onStart && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onStart();
              }}
              className="flex items-center gap-1 px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-xs font-medium rounded-lg transition-colors"
            >
              <PlayIcon className="w-3 h-3" />
              Start
            </button>
          )}

          {canPause && onPause && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onPause();
              }}
              className="flex items-center gap-1 px-3 py-1 bg-yellow-600 hover:bg-yellow-700 text-white text-xs font-medium rounded-lg transition-colors"
            >
              <PauseIcon className="w-3 h-3" />
              Pause
            </button>
          )}
        </div>

        {/* Configure Button */}
        {onConfigure && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onConfigure();
            }}
            className="p-1 text-gray-400 hover:text-gray-200 hover:bg-gray-700 rounded transition-colors"
          >
            <SettingsIcon className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Selection Indicator */}
      {isSelected && (
        <div className="absolute -top-1 -right-1 w-4 h-4 bg-copilot-blue rounded-full border-2 border-gray-900" />
      )}
    </div>
  );
}

export default AgentCard;
