// Cartrita AI OS - Streaming Indicator Component
// Animated indicator for real-time message streaming

'use client'

import { motion } from 'framer-motion'
import { Bot, Zap, Loader2 } from 'lucide-react'
import { cn } from '@/utils'
import { Badge } from '@/components/ui'
import { useAtomValue } from 'jotai'
import { selectedAgentAtom } from '@/stores'

// Typing animation dots
function TypingDots() {
  return (
    <div className="flex items-center gap-1">
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className="w-2 h-2 bg-current rounded-full"
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.5, 1, 0.5]
          }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            delay: i * 0.2
          }}
        />
      ))}
    </div>
  )
}

// Pulsing avatar
function PulsingAvatar({ children, isActive }: { children: React.ReactNode; isActive: boolean }) {
  return (
    <motion.div
      animate={isActive ? {
        scale: [1, 1.1, 1],
        opacity: [0.8, 1, 0.8]
      } : {}}
      transition={{
        duration: 2,
        repeat: Infinity,
        ease: 'easeInOut'
      }}
      className="relative"
    >
      {children}
      {isActive && (
        <motion.div
          className="absolute inset-0 rounded-full border-2 border-primary"
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.5, 0, 0.5]
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: 'easeInOut'
          }}
        />
      )}
    </motion.div>
  )
}

// Waveform animation for audio-like streaming
function StreamingWaveform() {
  return (
    <div className="flex items-center gap-1">
      {[0, 1, 2, 3, 4].map((i) => (
        <motion.div
          key={i}
          className="w-1 bg-primary rounded-full"
          animate={{
            height: [4, 16, 4],
            opacity: [0.3, 1, 0.3]
          }}
          transition={{
            duration: 1,
            repeat: Infinity,
            delay: i * 0.1,
            ease: 'easeInOut'
          }}
        />
      ))}
    </div>
  )
}

// Main Streaming Indicator Component
interface StreamingIndicatorProps {
  variant?: 'default' | 'compact' | 'minimal'
  showAgent?: boolean
  showStats?: boolean
  className?: string
}

export function StreamingIndicator({
  variant = 'default',
  showAgent = true,
  showStats = false,
  className
}: StreamingIndicatorProps) {
  const selectedAgent = useAtomValue(selectedAgentAtom)

  if (variant === 'minimal') {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className={cn('flex items-center gap-2 text-muted-foreground', className)}
      >
        <Loader2 className="h-4 w-4 animate-spin" />
        <span className="text-sm">Thinking...</span>
      </motion.div>
    )
  }

  if (variant === 'compact') {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.8 }}
        className={cn('flex items-center gap-2', className)}
      >
        <PulsingAvatar isActive={true}>
          <Bot className="h-5 w-5 text-primary" />
        </PulsingAvatar>
        <TypingDots />
      </motion.div>
    )
  }

  // Default variant
  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className={cn(
        'flex items-center justify-between p-3 bg-muted/50 rounded-lg border',
        className
      )}
    >
      <div className="flex items-center gap-3">
        <PulsingAvatar isActive={true}>
          <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
            <Bot className="h-4 w-4 text-primary-foreground" />
          </div>
        </PulsingAvatar>

        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">
              {selectedAgent?.name || 'AI Agent'} is thinking
            </span>
            <TypingDots />
          </div>

          {showAgent && selectedAgent && (
            <div className="flex items-center gap-2">
              <div className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 bg-secondary text-secondary-foreground">
                {selectedAgent.type}
              </div>
              <span className="text-xs text-muted-foreground">
                {selectedAgent.model}
              </span>
            </div>
          )}
        </div>
      </div>

      {showStats && (
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <Zap className="h-3 w-3" />
            <StreamingWaveform />
          </div>
          <span>Streaming</span>
        </div>
      )}
    </motion.div>
  )
}

// Inline streaming indicator for message bubbles
export function InlineStreamingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex items-center gap-2 text-muted-foreground"
    >
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
      >
        <Loader2 className="h-3 w-3" />
      </motion.div>
      <span className="text-xs">Generating response...</span>
    </motion.div>
  )
}

// Full-screen streaming overlay
export function StreamingOverlay({
  message = 'Processing your request...',
  showProgress = false,
  progress = 0
}: {
  message?: string
  showProgress?: boolean
  progress?: number
}) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center"
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="bg-background border rounded-lg p-6 shadow-lg max-w-sm w-full mx-4"
      >
        <div className="flex flex-col items-center gap-4 text-center">
          <PulsingAvatar isActive={true}>
            <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center">
              <Bot className="h-6 w-6 text-primary-foreground" />
            </div>
          </PulsingAvatar>

          <div className="space-y-2">
            <h3 className="text-lg font-semibold">Processing</h3>
            <p className="text-muted-foreground">{message}</p>
          </div>

          {showProgress && (
            <div className="w-full space-y-2">
              <div className="w-full bg-muted rounded-full h-2">
                <motion.div
                  className="bg-primary h-2 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.5 }}
                />
              </div>
              <p className="text-xs text-muted-foreground">{progress}% complete</p>
            </div>
          )}

          <StreamingWaveform />
        </div>
      </motion.div>
    </motion.div>
  )
}

// Streaming stats component
export function StreamingStats({
  tokensPerSecond = 0,
  totalTokens = 0,
  elapsedTime = 0
}: {
  tokensPerSecond?: number
  totalTokens?: number
  elapsedTime?: number
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-center gap-4 text-xs text-muted-foreground bg-muted/30 rounded-lg px-3 py-2"
    >
      <div className="flex items-center gap-1">
        <Zap className="h-3 w-3" />
        <span>{tokensPerSecond.toFixed(1)} t/s</span>
      </div>

      <div className="flex items-center gap-1">
        <span>{totalTokens} tokens</span>
      </div>

      <div className="flex items-center gap-1">
        <span>{elapsedTime.toFixed(1)}s</span>
      </div>
    </motion.div>
  )
}