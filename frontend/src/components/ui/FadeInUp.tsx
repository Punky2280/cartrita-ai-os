/**
 * FadeInUp Animation Component - Cartrita AI OS v2
 *
 * Reusable animation wrapper for smooth entrance effects
 */

import React, { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface FadeInUpProps {
  children: ReactNode;
  delay?: number;
  duration?: number;
  className?: string;
}

export function FadeInUp({
  children,
  delay = 0,
  duration = 300,
  className
}: FadeInUpProps) {
  return (
    <div
      className={cn(
        'animate-fade-in-up',
        className
      )}
      style={{
        animationDelay: `${delay}ms`,
        animationDuration: `${duration}ms`
      }}
    >
      {children}
    </div>
  );
}

export default FadeInUp;
