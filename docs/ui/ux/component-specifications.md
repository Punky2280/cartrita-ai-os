# Component Specification - Cartrita AI OS v2

## Overview

This document provides detailed specifications for all UI components in the Cartrita AI OS v2 frontend redesign.

## Base Component System

### Design Tokens

```typescript
// Design tokens following the distributed AI instructions pattern
export const tokens = {
  colors: {
    primary: {
      50: '#eff6ff',
      500: '#6e81ff', // Copilot Blue
      900: '#1e3a8a',
    },
    semantic: {
      success: '#10b981',
      warning: '#f59e0b',
      error: '#ef4444',
      info: '#3b82f6',
    },
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '3rem',
  },
  borderRadius: {
    sm: '0.25rem',
    md: '0.5rem',
    lg: '0.75rem',
    full: '9999px',
  },
  shadows: {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1)',
  },
};
```

## Message Components

### MessageBubble

```typescript
interface MessageBubbleProps {
  message: Message;
  variant: 'user' | 'assistant' | 'system' | 'agent';
  isStreaming?: boolean;
  onReaction?: (emoji: string) => void;
  onEdit?: (content: string) => void;
  onDelete?: () => void;
}

const MessageBubble = ({ message, variant, isStreaming = false }: MessageBubbleProps) => {
  const bubbleStyles = {
    user: 'bg-gradient-to-r from-copilot-blue to-copilot-pink text-white',
    assistant: 'bg-gray-800 text-gray-100 border border-gray-700',
    system: 'bg-orange-900/20 text-orange-200 border border-orange-800',
    agent: 'bg-blue-900/20 text-blue-200 border border-blue-800',
  };

  return (
    <div className={`
      max-w-3xl p-4 rounded-lg shadow-sm
      ${bubbleStyles[variant]}
      ${isStreaming ? 'animate-pulse' : ''}
    `}>
      <MessageContent content={message.content} />
      {message.metadata?.attachments && (
        <AttachmentList attachments={message.metadata.attachments} />
      )}
      <MessageActions onReaction={onReaction} onEdit={onEdit} onDelete={onDelete} />
    </div>
  );
};
```

### StreamingIndicator

```typescript
const StreamingIndicator = () => (
  <div className="flex items-center space-x-2 text-sm text-gray-500">
    <div className="flex space-x-1">
      <div className="w-2 h-2 bg-copilot-blue rounded-full animate-bounce" />
      <div className="w-2 h-2 bg-copilot-pink rounded-full animate-bounce delay-100" />
      <div className="w-2 h-2 bg-anthropic-orange rounded-full animate-bounce delay-200" />
    </div>
    <span>AI is thinking...</span>
  </div>
);
```

## Input Components

### EnhancedMessageInput

```typescript
interface MessageInputProps {
  onSendMessage: (content: string, attachments?: File[]) => void;
  disabled?: boolean;
  placeholder?: string;
  maxLength?: number;
  showTokenCount?: boolean;
}

const EnhancedMessageInput = ({
  onSendMessage,
  disabled = false,
  placeholder = "Ask anything...",
  maxLength = 4000,
  showTokenCount = true
}: MessageInputProps) => {
  const [content, setContent] = useState('');
  const [attachments, setAttachments] = useState<File[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [content]);

  const handleSend = () => {
    if (content.trim()) {
      onSendMessage(content, attachments);
      setContent('');
      setAttachments([]);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border border-gray-700 rounded-lg bg-gray-800/50 backdrop-blur-sm">
      <textarea
        ref={textareaRef}
        value={content}
        onChange={(e) => setContent(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        maxLength={maxLength}
        className="w-full p-4 bg-transparent text-white placeholder-gray-400 resize-none border-none outline-none min-h-[50px] max-h-[200px]"
        rows={1}
      />

      {attachments.length > 0 && (
        <AttachmentPreview
          attachments={attachments}
          onRemove={(index) => setAttachments(prev => prev.filter((_, i) => i !== index))}
        />
      )}

      <div className="flex items-center justify-between p-3 border-t border-gray-700">
        <div className="flex items-center space-x-2">
          <FileUploadButton onFilesSelected={setAttachments} />
          <VoiceInputButton onVoiceInput={(text) => setContent(prev => prev + text)} />
          <AgentSelectorButton />
        </div>

        <div className="flex items-center space-x-3">
          {showTokenCount && (
            <TokenCounter content={content} maxTokens={4000} />
          )}
          <SendButton
            onClick={handleSend}
            disabled={disabled || !content.trim()}
          />
        </div>
      </div>
    </div>
  );
};
```

## Agent Components

### AgentCard

```typescript
interface AgentCardProps {
  agent: Agent;
  isSelected?: boolean;
  onSelect?: (agentId: string) => void;
  showCapabilities?: boolean;
}

const AgentCard = ({ agent, isSelected = false, onSelect, showCapabilities = true }: AgentCardProps) => {
  const statusColors = {
    available: 'text-green-400 bg-green-400/20',
    busy: 'text-yellow-400 bg-yellow-400/20',
    offline: 'text-gray-400 bg-gray-400/20',
  };

  return (
    <div
      className={`
        p-4 rounded-lg border cursor-pointer transition-all duration-200
        ${isSelected
          ? 'border-copilot-blue bg-copilot-blue/10'
          : 'border-gray-700 bg-gray-800/50 hover:border-gray-600'
        }
      `}
      onClick={() => onSelect?.(agent.id)}
    >
      <div className="flex items-center space-x-3 mb-3">
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-copilot-blue to-copilot-pink flex items-center justify-center">
          <span className="text-white font-medium">{agent.name[0]}</span>
        </div>
        <div className="flex-1">
          <h3 className="font-medium text-white">{agent.name}</h3>
          <p className="text-sm text-gray-400">{agent.description}</p>
        </div>
        <div className={`px-2 py-1 rounded-full text-xs ${statusColors[agent.status]}`}>
          {agent.status}
        </div>
      </div>

      {showCapabilities && agent.capabilities.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {agent.capabilities.map(capability => (
            <span
              key={capability}
              className="px-2 py-1 text-xs bg-gray-700 text-gray-300 rounded-full"
            >
              {capability}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};
```

### AgentOrchestrator

```typescript
const AgentOrchestrator = () => {
  const [selectedAgents, setSelectedAgents] = useState<string[]>([]);
  const [activeWorkflow, setActiveWorkflow] = useState<Workflow | null>(null);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-white">Agent Orchestrator</h2>
        <WorkflowSelector onSelect={setActiveWorkflow} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {agents.map(agent => (
          <AgentCard
            key={agent.id}
            agent={agent}
            isSelected={selectedAgents.includes(agent.id)}
            onSelect={(agentId) => {
              setSelectedAgents(prev =>
                prev.includes(agentId)
                  ? prev.filter(id => id !== agentId)
                  : [...prev, agentId]
              );
            }}
          />
        ))}
      </div>

      {selectedAgents.length > 0 && (
        <AgentWorkflowPanel
          agents={selectedAgents}
          workflow={activeWorkflow}
          onExecute={handleWorkflowExecution}
        />
      )}
    </div>
  );
};
```

## Layout Components

### ResponsiveSidebar

```typescript
interface ResponsiveSidebarProps {
  side: 'left' | 'right';
  isOpen: boolean;
  onToggle: () => void;
  children: React.ReactNode;
  collapsedWidth?: number;
  expandedWidth?: number;
}

const ResponsiveSidebar = ({
  side,
  isOpen,
  onToggle,
  children,
  collapsedWidth = 64,
  expandedWidth = 320
}: ResponsiveSidebarProps) => {
  return (
    <aside
      className={`
        ${side === 'left' ? 'border-r' : 'border-l'} border-gray-700
        bg-gray-900/50 backdrop-blur-sm transition-all duration-300
        ${isOpen ? `w-[${expandedWidth}px]` : `w-[${collapsedWidth}px]`}
      `}
    >
      <div className="h-full flex flex-col">
        <div className="p-4 border-b border-gray-700">
          <button
            onClick={onToggle}
            className="w-full flex items-center justify-center p-2 rounded-lg hover:bg-gray-800 transition-colors"
          >
            {isOpen ? (
              side === 'left' ? <ChevronLeft /> : <ChevronRight />
            ) : (
              side === 'left' ? <ChevronRight /> : <ChevronLeft />
            )}
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {isOpen && children}
        </div>
      </div>
    </aside>
  );
};
```

## Utility Components

### LoadingSpinner

```typescript
interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  color?: 'primary' | 'secondary' | 'white';
}

const LoadingSpinner = ({ size = 'md', color = 'primary' }: LoadingSpinnerProps) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  const colorClasses = {
    primary: 'text-copilot-blue',
    secondary: 'text-copilot-pink',
    white: 'text-white',
  };

  return (
    <div className={`inline-block animate-spin rounded-full border-2 border-solid border-current border-r-transparent ${sizeClasses[size]} ${colorClasses[color]}`} />
  );
};
```

### TokenCounter

```typescript
interface TokenCounterProps {
  content: string;
  maxTokens: number;
  model?: string;
}

const TokenCounter = ({ content, maxTokens, model = 'gpt-4' }: TokenCounterProps) => {
  const tokenCount = useMemo(() => estimateTokens(content, model), [content, model]);
  const percentage = (tokenCount / maxTokens) * 100;

  const getColorClass = () => {
    if (percentage < 70) return 'text-green-400';
    if (percentage < 90) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <div className={`text-sm ${getColorClass()}`}>
      <span>{tokenCount}</span>
      <span className="text-gray-500">/{maxTokens}</span>
    </div>
  );
};
```

## Animation Components

### FadeInUp

```typescript
interface FadeInUpProps {
  children: React.ReactNode;
  delay?: number;
  duration?: number;
}

const FadeInUp = ({ children, delay = 0, duration = 0.3 }: FadeInUpProps) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration, delay }}
  >
    {children}
  </motion.div>
);
```

### SlideIn

```typescript
interface SlideInProps {
  children: React.ReactNode;
  direction: 'left' | 'right' | 'up' | 'down';
  distance?: number;
}

const SlideIn = ({ children, direction, distance = 50 }: SlideInProps) => {
  const getInitialPosition = () => {
    switch (direction) {
      case 'left': return { x: -distance, y: 0 };
      case 'right': return { x: distance, y: 0 };
      case 'up': return { x: 0, y: -distance };
      case 'down': return { x: 0, y: distance };
    }
  };

  return (
    <motion.div
      initial={{ ...getInitialPosition(), opacity: 0 }}
      animate={{ x: 0, y: 0, opacity: 1 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
    >
      {children}
    </motion.div>
  );
};
```

## Export Statement

```typescript
export {
  // Base components
  MessageBubble,
  StreamingIndicator,
  EnhancedMessageInput,

  // Agent components
  AgentCard,
  AgentOrchestrator,

  // Layout components
  ResponsiveSidebar,

  // Utility components
  LoadingSpinner,
  TokenCounter,

  // Animation components
  FadeInUp,
  SlideIn,
};
```
