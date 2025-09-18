/**
 * LoadingSpinner Component - Cartrita AI OS v2
 *
 * Animated loading indicator with Cartrita branding
 */

import React from 'react';
import { cn } from '@/lib/utils';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  message?: string;
}

const sizeClasses = {
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-8 h-8'
};

export function LoadingSpinner({
  size = 'md',
  className,
  message
}: LoadingSpinnerProps) {
  return (
    <div className={cn('flex flex-col items-center gap-2', className)}>
      <div className="relative">
        <div className={cn(
          'rounded-full border-2 border-gray-700 animate-spin',
          sizeClasses[size]
        )}>
          <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-copilot-blue" />
        </div>
      </div>
      {message && (
        <p className="text-sm text-gray-400">
          {message}
        </p>
      )}
    </div>
  );
}

export default LoadingSpinner;
