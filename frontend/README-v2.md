# Cartrita AI OS v2 Frontend

A modern, responsive Next.js 15 application for AI agent orchestration and multi-agent chat collaboration.

## 🚀 Features

- **Modern Tech Stack**: Next.js 15, TypeScript 5.3+, Tailwind CSS 3.4+
- **State Management**: Jotai for client state, TanStack Query for server state
- **Real-time Streaming**: Server-Sent Events (SSE) for live chat updates
- **Multi-Agent Support**: Orchestrate multiple AI agents with different capabilities
- **Responsive Design**: Three-column layout with collapsible sidebar and right panel
- **Component Library**: Comprehensive set of reusable UI components
- **Animation System**: Framer Motion integration with custom Cartrita animations
- **Theme System**: Dark mode with Cartrita brand colors and design tokens

## 🏗️ Architecture

### Component Structure
```
src/components/
├── messages/          # Chat interface components
│   ├── MessageBubble          # Individual message display with role-based styling
│   ├── StreamingIndicator     # Real-time AI response indicator
│   └── EnhancedMessageInput   # Advanced input with attachments & agent selection
├── agents/            # Agent management components
│   ├── AgentCard             # Individual agent display with status & metrics
│   └── AgentOrchestrator     # Multi-agent management interface
├── layout/            # Application layout components
│   ├── ResponsiveSidebar     # Collapsible navigation sidebar
│   └── ApplicationShell      # Main three-column layout container
├── conversations/     # Conversation management
│   └── ConversationList      # Searchable conversation history
├── ui/               # Base UI components
│   ├── FadeInUp             # Smooth entrance animations
│   ├── LoadingSpinner       # Branded loading indicators
│   └── ErrorBoundary        # Graceful error handling
└── pages/            # Full-page components
    ├── ChatPage             # Main chat interface
    ├── AgentsPage           # Agent management dashboard
    └── SettingsPage         # User preferences & configuration
```

### State Management
```
src/lib/store/
├── atoms.ts           # Jotai client state atoms
├── queries.ts         # TanStack Query hooks
├── service.ts         # API service layer
└── streaming.ts       # SSE streaming hooks
```

### Design System
```
src/lib/
├── tokens.ts          # Design tokens (colors, spacing, typography)
├── utils.ts           # Utility functions (cn, formatters)
└── styles/
    └── globals-v2.css # Global styles with component classes
```

## 🎨 Design System

### Brand Colors
- **Copilot Blue**: `#6e81ff` - Primary brand color
- **Copilot Pink**: `#e568ac` - Secondary brand color
- **Anthropic Orange**: `#d97e21` - Accent color
- **Gray Scale**: Modern dark theme with consistent gray palette

### Component Patterns
- **Message Bubbles**: Role-based styling (user, assistant, system, agent)
- **Agent Cards**: Status indicators, metrics, interactive controls
- **Responsive Layout**: Mobile-first with progressive enhancement
- **Animation System**: Consistent entrance effects and micro-interactions

## 🔧 Development

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation
```bash
cd frontend
npm install
```

### Development Server
```bash
npm run dev
```

### Build for Production
```bash
npm run build
npm run start
```

### Type Checking
```bash
npm run type-check
```

### Linting
```bash
npm run lint
npm run lint:fix
```

## 📦 Key Dependencies

### Core Framework
- **Next.js 15**: React framework with App Router
- **TypeScript 5.3+**: Type safety and developer experience
- **React 18**: Latest React with concurrent features

### State Management
- **Jotai v2**: Atomic state management for client state
- **TanStack Query v5**: Server state management with caching
- **Persistent Storage**: Local storage integration for user preferences

### Styling & UI
- **Tailwind CSS 3.4+**: Utility-first CSS framework
- **Framer Motion v11**: Animation and gesture library
- **Lucide React**: Modern icon library
- **Custom Design System**: Cartrita brand tokens and components

### Developer Experience
- **ESLint**: Code linting with Next.js and TypeScript rules
- **Prettier**: Code formatting
- **TypeScript**: Full type coverage across application

## 🌐 API Integration

### Endpoints
```typescript
// Base API URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Main endpoints
/api/v1/conversations     # Chat management
/api/v1/agents           # Agent orchestration
/api/v1/messages         # Message operations
/api/v1/stream/{id}      # SSE streaming
/api/v1/files/upload     # File attachments
```

### Authentication
- JWT token-based authentication
- Automatic token refresh
- Secure local storage handling

## 📱 Responsive Design

### Breakpoints
- **Mobile**: `< 768px` - Single column with mobile navigation
- **Tablet**: `768px - 1024px` - Two columns with collapsible sidebar
- **Desktop**: `> 1024px` - Three columns with full layout

### Layout Behavior
- **Sidebar**: Collapsible on desktop, overlay on mobile
- **Right Panel**: Auto-hide on smaller screens, context-aware content
- **Chat Interface**: Responsive message bubbles and input areas

## 🧪 Testing Strategy

### Component Testing
- **Vitest**: Unit testing for components and utilities
- **React Testing Library**: Component interaction testing
- **MSW**: API mocking for integration tests

### Storybook Integration
- Component documentation and visual testing
- Interactive component playground
- Design system showcase

## 🚀 Performance Optimizations

### Bundle Optimization
- **Tree Shaking**: Eliminate unused code
- **Code Splitting**: Route-based and component-based splitting
- **Image Optimization**: Next.js Image component with WebP

### Runtime Performance
- **React Concurrent**: Automatic batching and transitions
- **Query Caching**: Intelligent server state caching with TanStack Query
- **Streaming**: Real-time updates without full re-renders
- **Virtualization**: Large list performance optimization

## 📚 Component Documentation

Each component includes:
- **TypeScript Interfaces**: Full prop type definitions
- **JSDoc Comments**: Usage examples and parameter descriptions
- **Accessibility**: ARIA labels and keyboard navigation
- **Error Boundaries**: Graceful failure handling

### Example Usage
```tsx
import { MessageBubble } from '@/components/messages';

<MessageBubble
  id="msg-123"
  role="assistant"
  content="Hello! How can I help you today?"
  timestamp="2024-01-15T10:30:00Z"
  agentName="Coding Assistant"
  isStreaming={false}
  onReact={(emoji) => handleReaction(emoji)}
/>
```

## 🔄 State Flow

### Client State (Jotai)
- User preferences and settings
- UI state (sidebar collapse, modal visibility)
- Current conversation and agent selection
- Local conversation history

### Server State (TanStack Query)
- API data with caching and synchronization
- Optimistic updates for better UX
- Background refetching and error recovery
- Real-time streaming integration

## 🎯 Future Roadmap

### Planned Features
- [ ] **Voice Integration**: Speech-to-text and text-to-speech
- [ ] **File Management**: Drag-and-drop file uploads and preview
- [ ] **Plugin System**: Extensible agent capabilities
- [ ] **Multi-workspace**: Support for multiple project contexts
- [ ] **Collaboration**: Real-time multi-user editing
- [ ] **Mobile App**: React Native companion application

### Technical Improvements
- [ ] **Service Worker**: Offline functionality and caching
- [ ] **WebRTC**: Direct peer-to-peer communication
- [ ] **WebAssembly**: High-performance computation modules
- [ ] **Progressive Web App**: Mobile app-like experience

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📞 Support

For questions and support, please visit our documentation or create an issue in the repository.
