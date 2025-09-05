# Cartrita AI OS - Frontend

A modern, ChatGPT-like frontend for the Cartrita AI Operating System built with React 18, Next.js 15, and TypeScript.

## 🚀 Features

- **ChatGPT-like Interface**: Pixel-perfect replica with enhanced Cartrita AI OS capabilities
- **Multi-Agent Support**: Interact with 15+ specialized AI agents
- **Real-time Streaming**: Live message streaming with typing indicators
- **Voice Input/Output**: Advanced voice recording and transcription
- **File Upload**: Drag-and-drop file handling with progress tracking
- **Global Search**: Search across conversations, messages, agents, and files
- **Advanced Settings**: Comprehensive user preferences and API key management
- **Responsive Design**: Mobile-first design with dark/light theme support
- **Type Safety**: Full TypeScript coverage with strict mode
- **Performance**: Optimized with React Query, Jotai, and Framer Motion

## 🛠️ Tech Stack

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript 5.3
- **Styling**: Tailwind CSS 3.4
- **State Management**: Jotai v2
- **Data Fetching**: TanStack Query v5
- **Animations**: Framer Motion v11
- **Icons**: Lucide React
- **Forms**: React Hook Form + Zod
- **Real-time**: Socket.IO Client v4
- **Build Tool**: Biome (linting/formatting)

## 📦 Installation

1. **Install Dependencies**

   ```bash
   npm install
   # or
   yarn install
   # or
   pnpm install
   ```

2. **Environment Setup**

   ```bash
   cp .env.example .env.local
   ```

   Configure your environment variables:

   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_WS_URL=ws://localhost:8000
   NEXT_PUBLIC_APP_NAME=Cartrita AI OS
   NEXT_PUBLIC_APP_VERSION=2.0.0
   ```

3. **Start Development Server**

   ```bash
   npm run dev
   # or
   yarn dev
   # or
   pnpm dev
   ```

4. **Open Browser**

   Navigate to [http://localhost:3000](http://localhost:3000)

## 🏗️ Project Structure

```text
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx           # Home page
│   │   └── globals.css        # Global styles
│   ├── components/            # React components
│   │   ├── ui/                # Reusable UI components
│   │   ├── ChatInterface.tsx  # Main chat interface
│   │   ├── MessageBubble.tsx  # Message display component
│   │   ├── AgentSelector.tsx  # Agent selection interface
│   │   ├── StreamingIndicator.tsx # Streaming UI
│   │   ├── VoiceInput.tsx     # Voice input component
│   │   ├── FileUpload.tsx     # File upload component
│   │   ├── SearchInterface.tsx # Global search interface
│   │   └── SettingsPanel.tsx  # Settings panel
│   ├── hooks/                 # Custom React hooks
│   │   └── index.ts           # All hooks
│   ├── services/              # API and external services
│   │   └── api.ts             # API client
│   ├── stores/                # Jotai atoms
│   │   └── index.ts           # State management
│   ├── types/                 # TypeScript type definitions
│   │   └── index.ts           # All types
│   └── utils/                 # Utility functions
│       └── index.ts           # Helper functions
├── public/                    # Static assets
├── next.config.js             # Next.js configuration
├── tailwind.config.js         # Tailwind CSS configuration
├── tsconfig.json              # TypeScript configuration
├── biome.json                 # Biome configuration
└── package.json               # Dependencies and scripts
```

## 🎯 Key Components

### ChatInterface

The main chat interface with ChatGPT-like layout:

- Sidebar with conversation history
- Main chat area with message bubbles
- Input field with send button
- Agent selector and settings

### MessageBubble

Enhanced message display with:

- Markdown rendering
- Code syntax highlighting
- Copy/edit/delete actions
- Streaming indicators
- File attachments

### AgentSelector

Agent selection interface with:

- Agent cards with performance metrics
- Search and filtering
- Real-time status indicators
- Performance comparison

### VoiceInput

Advanced voice input with:

- Recording visualization
- Real-time transcription
- Audio analysis
- Error handling

### FileUpload

Comprehensive file handling:

- Drag-and-drop interface
- Progress tracking
- File type validation
- Preview functionality

### SearchInterface

Global search across all content:

- Real-time search results
- Type filtering
- Date range filtering
- Result highlighting

### SettingsPanel

Comprehensive settings with:

- Profile management
- API key configuration
- Appearance customization
- Notification preferences
- Privacy settings
- Data export/import

## 🔧 Development

### Available Scripts

```bash
# Development
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run preview      # Preview production build

# Code Quality
npm run lint         # Run Biome linter
npm run lint:fix     # Fix linting issues
npm run format       # Format code with Biome
npm run type-check   # Run TypeScript type checking

# Testing
npm run test         # Run tests
npm run test:watch   # Run tests in watch mode
npm run test:coverage # Run tests with coverage

# Database
npm run db:generate  # Generate database types
npm run db:push      # Push database schema
npm run db:migrate   # Run database migrations
```

### Code Quality Standards

- **TypeScript**: Strict mode enabled
- **Linting**: Biome with comprehensive rules
- **Formatting**: Consistent code formatting
- **Testing**: Comprehensive test coverage
- **Performance**: Optimized bundle size and loading

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | Yes |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL | Yes |
| `NEXT_PUBLIC_APP_NAME` | Application name | No |
| `NEXT_PUBLIC_APP_VERSION` | Application version | No |

## 🚀 Deployment

### Build for Production

```bash
npm run build
```

### Docker Deployment

```bash
# Build Docker image
docker build -t cartrita-frontend .

# Run container
docker run -p 3000:3000 cartrita-frontend
```

### Environment Configuration

For production deployment, ensure these environment variables are set:

```env
NEXT_PUBLIC_API_URL=https://api.cartrita.com
NEXT_PUBLIC_WS_URL=wss://api.cartrita.com
NEXT_PUBLIC_APP_NAME=Cartrita AI OS
NEXT_PUBLIC_APP_VERSION=2.0.0
```

## 🔒 Security

- API keys are encrypted and never exposed in logs
- All user data is handled securely
- Input validation on all forms
- XSS protection with proper sanitization
- CSRF protection enabled

## 📱 Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:

- Create an issue on GitHub
- Check the documentation
- Join our Discord community

## 🎉 Acknowledgments

- Built with Next.js and React
- Inspired by ChatGPT's excellent UX
- Powered by the Cartrita AI OS backend
