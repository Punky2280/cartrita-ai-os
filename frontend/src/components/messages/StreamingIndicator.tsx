/**
 * StreamingIndicator Component - Cartrita AI OS v2
 *
 * Animated indicator showing AI is processing with bouncing dots
 * in Cartrita brand colors
 */

import React from 'react';
import { cn } from '@/lib/utils';

interface StreamingIndicatorProps {
  className?: string;
  message?: string;
}

export function StreamingIndicator({
  className,
  message = "AI is thinking..."
}: StreamingIndicatorProps) {
  return (
    <div className={cn(
      'flex items-center gap-3 p-4 rounded-lg bg-gray-800/50 border border-gray-700 backdrop-blur-sm',
      className
    )}>
      {/* Avatar */}
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-xs font-semibold text-gray-200">
        AI
      </div>

      {/* Content */}
      <div className="flex items-center gap-3">
        {/* Bouncing Dots */}
        <div className="flex items-center space-x-1">
          <div
            className="w-2 h-2 bg-copilot-blue rounded-full animate-bounce-dots"
            style={{ animationDelay: '0s' }}
          />
          <div
            className="w-2 h-2 bg-copilot-pink rounded-full animate-bounce-dots"
            style={{ animationDelay: '0.2s' }}
          />
          <div
            className="w-2 h-2 bg-anthropic-orange rounded-full animate-bounce-dots"
            style={{ animationDelay: '0.4s' }}
          />
        </div>

        {/* Message Text */}
        <span className="text-sm text-gray-300 font-medium">
          {message}
        </span>
      </div>
    </div>
  );
}

export default StreamingIndicator;
