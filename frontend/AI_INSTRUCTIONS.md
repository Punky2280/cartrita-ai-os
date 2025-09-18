# AI Instructions: Frontend Development

## Next.js 15 Architecture

**Core Structure:**
- `src/components/` - Reusable UI components
- `src/pages/` - Next.js pages and API routes
- `src/hooks/` - Custom React hooks for server state (TanStack Query)
- `src/stores/` - Client state atoms (Jotai)
- `src/services/` - API client functions
- `src/types/` - TypeScript definitions

## State Management Pattern

**Client State - Use Jotai Atoms:**

```typescript
// src/stores/index.ts
import { atom } from "jotai";
import { atomWithStorage } from "jotai/utils";

// Persistent client state
export const userPreferencesAtom = atomWithStorage("userPrefs", {
  theme: "system",
  language: "en"
});

// Ephemeral UI state
export const chatInputAtom = atom("");
export const sidebarOpenAtom = atom(true);
```

**Server State - Use TanStack Query:**

```typescript
// src/hooks/useChat.ts
import { useQuery, useMutation } from "@tanstack/react-query";

export const useConversations = () => {
  return useQuery({
    queryKey: ["conversations"],
    queryFn: () => api.getConversations(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useSendMessage = () => {
  return useMutation({
    mutationFn: (message: string) => api.sendMessage(message),
    onSuccess: () => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });
};
```

## SSE Streaming Integration

**SSE Hook Pattern:**

```typescript
// src/hooks/useSSEChat.ts
export const useSSEChat = (conversationId: string) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const eventSource = new EventSource(`/api/chat/stream/${conversationId}`);

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'message_chunk') {
        // Append semantics - never replace
        setMessages(prev => appendToLastMessage(prev, data.content));
      } else if (data.type === 'done') {
        // Stream completed
        setIsConnected(false);
      }
    };

    return () => eventSource.close();
  }, [conversationId]);

  return { messages, isConnected };
};
```

## Component Patterns

**Modern React TypeScript - No React.FC:**

```typescript
// src/components/ChatMessage.tsx
interface ChatMessageProps {
  message: Message;
  isStreaming?: boolean;
  onRetry?: () => void;
}

export default function ChatMessage({
  message,
  isStreaming = false,
  onRetry
}: ChatMessageProps) {
  return (
    <div className="chat-message">
      <div className="content">{message.content}</div>
      {isStreaming && <StreamingIndicator />}
    </div>
  );
}
```

**State Integration:**

```typescript
// Using both Jotai and TanStack Query
import { useAtom } from "jotai";
import { useQuery } from "@tanstack/react-query";
import { userPreferencesAtom } from "@/stores";

export default function ChatInterface() {
  const [preferences] = useAtom(userPreferencesAtom);
  const { data: conversations, isLoading } = useQuery({
    queryKey: ["conversations"],
    queryFn: api.getConversations,
  });

  return (
    <div className={`chat-interface theme-${preferences.theme}`}>
      {/* Component content */}
    </div>
  );
}
```

## API Client Structure

**Service Layer Pattern:**

```typescript
// src/services/api.ts
import axios from "axios";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  timeout: 10000,
});

export const chatAPI = {
  sendMessage: async (message: string, conversationId?: string) => {
    const response = await api.post("/chat/send", {
      message,
      conversation_id: conversationId
    });
    return response.data;
  },

  getConversations: async () => {
    const response = await api.get("/conversations");
    return response.data;
  },

  // SSE endpoint for streaming
  streamChat: (conversationId: string) =>
    `/api/chat/stream/${conversationId}`,
};
```

## Testing Patterns

**Component Testing with Vitest:**

```typescript
// src/__tests__/components/ChatMessage.test.tsx
import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import ChatMessage from "@/components/ChatMessage";

test("renders message content", () => {
  const message = { id: "1", content: "Hello world", role: "user" };

  render(<ChatMessage message={message} />);

  expect(screen.getByText("Hello world")).toBeInTheDocument();
});

test("shows streaming indicator when streaming", () => {
  const message = { id: "1", content: "Partial...", role: "assistant" };

  render(<ChatMessage message={message} isStreaming />);

  expect(screen.getByTestId("streaming-indicator")).toBeInTheDocument();
});
```

**Hook Testing:**

```typescript
// src/__tests__/hooks/useSSEChat.test.ts
import { renderHook, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { useSSEChat } from "@/hooks/useSSEChat";

// Mock EventSource
global.EventSource = vi.fn();

test("establishes SSE connection", async () => {
  const { result } = renderHook(() => useSSEChat("conv-123"));

  await waitFor(() => {
    expect(result.current.isConnected).toBe(true);
  });
});
```

## Development Commands

```bash
# Development server
npm run dev

# Type checking
npm run type-check

# Testing
npm run test
npm run test:watch
npm run test:coverage

# Linting
npm run lint:fix

# Build
npm run build
```

## Environment Configuration

```typescript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    API_URL: process.env.API_URL || "http://localhost:8000",
  },
  experimental: {
    // Next.js 15 features
    ppr: true, // Partial Prerendering
  },
};

export default nextConfig;
```

## Styling with Tailwind

**Component Styling:**

```typescript
import { cva } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md text-sm font-medium",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "secondary";
  size?: "default" | "sm" | "lg";
}

export default function Button({
  className,
  variant,
  size,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  );
}
```

## Performance Guidelines

- **Use React.memo for expensive components**
- **Implement virtualization for long lists**
- **Lazy load components with dynamic imports**
- **Optimize images with Next.js Image component**
- **Use useMemo/useCallback judiciously - profile first**

## Error Boundaries

```typescript
// src/components/ErrorBoundary.tsx
import React from "react";

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends React.Component<
  React.PropsWithChildren<{}>,
  ErrorBoundaryState
> {
  constructor(props: React.PropsWithChildren<{}>) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Error caught by boundary:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-fallback">
          <h2>Something went wrong</h2>
          <p>{this.state.error?.message}</p>
        </div>
      );
    }

    return this.props.children;
  }
}
```

## Security Considerations

- **Never store API keys in client code**
- **Use environment variables for configuration**
- **Validate all user inputs**
- **Sanitize HTML content before rendering**
- **Use HTTPS in production**
- **Implement proper CORS headers**
