// Cartrita AI OS - Modern Chat Interface
// Redesigned ChatGPT-like interface with proper architecture

import { useState, useEffect, useRef, useCallback } from 'react'
import { useAtom, useAtomValue, useSetAtom } from 'jotai'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import SettingsModal from '@/components/SettingsModal'
import AttachmentsBar, { AttachmentItem } from '@/components/AttachmentsBar'
import MessageList, { type ChatMessage as MLMessage } from '@/components/MessageList'
import {
  Send,
  Settings,
  Menu,
  Mic,
  MicOff,
  Paperclip,
  MoreVertical,
  Bot,
  X,
  Loader2,
  Search,
  BarChart3,
  Volume2,
  Plus,
  MessageSquare
} from 'lucide-react'
import { cn } from '@/utils'
import {
  currentConversationAtom,
  conversationsAtom,
  currentMessagesAtom,
  messagesAtom,
  selectedAgentAtom,
  selectedAgentIdAtom,
  agentsAtom,
  currentConversationIdAtom,
  sidebarOpenAtom,
  chatInputAtom,
  isStreamingAtom,
  streamingMessageAtom,
  userAtom,
  themeAtom,
  settingsAtom,
  featureFlagsAtom
} from '@/stores'
import { streamingService } from '@/services/streaming'
// Narrow type helper (Message already strongly typed; kept for safety in functional updates)
const isMessage = (val: unknown): val is Message => !!val && typeof val === 'object' && 'role' in (val as any) && 'content' in (val as any)
import { apiClient } from '@/services/api'
import type { Message, Agent, ChatRequest, Conversation } from '@/types'

// Components
import {
  Textarea,
  ScrollArea,
  Avatar,
  AvatarFallback,
  Badge,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
  Button
} from '@/components/ui'
import { Dialog } from '@/components/ui'
import { FileUploader } from '@/components/ui'
import { Progress } from '@/components/ui'
import { RealtimeService } from '@/services/realtime/socket'
import AgentTaskTimeline from '@/components/AgentTaskTimeline'

interface VoiceState {
  isRecording: boolean
  isProcessing: boolean
  currentTranscription: string
  audioLevel: number
}

// Main Chat Interface Component
export default function ChatInterface() {
  // Core state
  const [sidebarOpen, setSidebarOpen] = useAtom(sidebarOpenAtom)
  const [chatInput, setChatInput] = useAtom(chatInputAtom)
  const [attachments, setAttachments] = useState<AttachmentItem[]>([])
  const [showSettings, setShowSettings] = useState(false)
  const [showSearch, setShowSearch] = useState(false)
  const [voiceState, setVoiceState] = useState<VoiceState>({
    isRecording: false,
    isProcessing: false,
    currentTranscription: '',
    audioLevel: 0
  })
  const [showUploadDialog, setShowUploadDialog] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [typingUsers, setTypingUsers] = useState<Record<string, boolean>>({})
  const [agentEvents, setAgentEvents] = useState<{ id: string; status: 'started' | 'progress' | 'completed'; progress?: number }[]>([])
  const typingTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const realtimeRef = useRef<RealtimeService | null>(null)

  // Atom values
  const user = useAtomValue(userAtom)
  const theme = useAtomValue(themeAtom)
  const settings = useAtomValue(settingsAtom)
  const featureFlags = useAtomValue(featureFlagsAtom)
  const currentConversation = useAtomValue(currentConversationAtom)
  const conversations = useAtomValue(conversationsAtom)
  const messages = useAtomValue(currentMessagesAtom)
  const selectedAgent = useAtomValue(selectedAgentAtom)
  const agents = useAtomValue(agentsAtom)
  const isStreaming = useAtomValue(isStreamingAtom)
  
  // Atom setters
  const [streamingMessage, setStreamingMessage] = useAtom(streamingMessageAtom) as [Message | null, (value: Message | null) => void]
  const streamingRef = useRef<Message | null>(null)
  useEffect(() => { streamingRef.current = streamingMessage }, [streamingMessage])
  const [userAutoScroll, setUserAutoScroll] = useState(true)

  // Abort controller state for UI abort button
  const abortRef = useRef<() => void>(() => {})
  
  // Get message setter for current conversation
  const setMessages = useSetAtom(
    currentConversation ? messagesAtom(currentConversation.id) : messagesAtom('default')
  )
  
  // Additional atom setters for initialization
  const setAgents = useSetAtom(agentsAtom)
  const setSelectedAgentId = useSetAtom(selectedAgentIdAtom)
  const setConversations = useSetAtom(conversationsAtom)
  const setCurrentConversationId = useSetAtom(currentConversationIdAtom)

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Initialize default data
  useEffect(() => {
    // Initialize default supervisor agent if none exists
    if (agents.length === 0) {
      const defaultAgent: Agent = {
        id: 'supervisor-default',
        name: 'Cartrita Supervisor',
        type: 'supervisor',
        status: 'idle',
        model: 'gpt-4',
        description: 'AI Assistant',
        capabilities: ['general', 'conversation'],
        metadata: {
          lastActive: new Date().toISOString(),
          totalRequests: 0,
          successRate: 100,
          averageResponseTime: 1000,
          specialties: ['General AI assistance'],
          limitations: []
        }
      }
      setAgents([defaultAgent])
      setSelectedAgentId(defaultAgent.id)
    } else if (!selectedAgent && agents.length > 0) {
      setSelectedAgentId(agents[0].id)
    }

    // Initialize default conversation if none exists
    if (conversations.length === 0) {
      const defaultConversation: Conversation = {
        id: 'default-conversation',
        title: 'New Chat',
        userId: 'default-user',
        messages: [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        isPinned: false,
        isArchived: false,
        tags: [],
        metadata: {
          totalMessages: 0,
          lastActivity: new Date().toISOString(),
          agentUsed: selectedAgent?.id || agents[0]?.id || 'supervisor-default',
          tokensUsed: 0,
          processingTime: 0
        }
      }
      setConversations([defaultConversation])
      setCurrentConversationId(defaultConversation.id)
    } else if (!currentConversation && conversations.length > 0) {
      setCurrentConversationId(conversations[0].id)
    }
  }, [agents, selectedAgent, conversations, currentConversation, setAgents, setSelectedAgentId, setConversations, setCurrentConversationId])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (settings.autoScroll && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, streamingMessage, settings.autoScroll])

  // Realtime: presence & typing wiring
  useEffect(() => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL as string | undefined
    if (!wsUrl) return
    // Initialize only once
    if (!realtimeRef.current) {
      // Temporarily disabled until Socket.IO backend is implemented
      // realtimeRef.current = new RealtimeService(wsUrl)
      // realtimeRef.current.onTyping((evt) => {
      //   if (!currentConversation?.id || evt.conversationId !== currentConversation.id) return
      //   setTypingUsers((prev) => ({ ...prev, [evt.userId]: evt.isTyping }))
      // })
    }
    return () => {
      // Do not disconnect globally on rerenders; cleanup at unmount only
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentConversation?.id])

  // Focus input when conversation changes
  useEffect(() => {
    if (currentConversation && inputRef.current) {
      inputRef.current.focus()
    }
  }, [currentConversation?.id])

  // Handle sending message
  const handleSendMessage = useCallback(async (overrideMessage?: string) => {
    const candidate = overrideMessage ?? chatInput
    if (!candidate.trim() || !selectedAgent || isStreaming) return

    const messageContent = candidate.trim()
    setChatInput('')

    const chatRequest: ChatRequest = {
      message: messageContent,
      conversation_id: currentConversation?.id,
      agent_override: selectedAgent.type,
      context: {
        timestamp: new Date().toISOString(),
        user_agent: navigator.userAgent,
        conversation_title: currentConversation?.title
      },
      stream: featureFlags.streaming
    }

    // Add user message to the conversation immediately
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: messageContent,
      conversationId: currentConversation?.id || 'default-conversation',
      metadata: {
        agent_type: selectedAgent.type
      },
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      isEdited: false
    }
    
    // Update messages state with user message
  setMessages((prev) => [...prev, userMessage])

    try {
      if (featureFlags.streaming) {
        // Initialize streaming message
        const assistantMessage: Message = {
          id: `assistant-${Date.now()}`,
          role: 'assistant', 
          content: '',
          conversationId: currentConversation?.id || 'default-conversation',
          metadata: {
            agent_type: selectedAgent.type
          },
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          isEdited: false
        }
        
        setStreamingMessage(assistantMessage)

        // Use streaming service
        const abortable = streamingService.streamChat(chatRequest, {
          onChunk: (chunk) => {
            const current = streamingRef.current
            if (current) {
              const updated = { ...current, content: (current.content || '') + chunk.content, updatedAt: new Date().toISOString() }
              setStreamingMessage(updated)
            }
          },
          onComplete: (response) => {
            console.log('Stream complete:', response.response)
            
            // Add final assistant message to conversation
            const finalMessage: Message = {
              id: `assistant-${Date.now()}-final`,
              role: 'assistant',
              content: response.response,
              conversationId: currentConversation?.id || 'default-conversation',
              metadata: {
                agent_type: selectedAgent.type,
                conversation_id: response.conversation_id
              },
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString(),
              isEdited: false
            }
            
            setMessages((prev) => [...prev, finalMessage])
            setStreamingMessage(null) // Clear streaming message
            toast.success('Message sent successfully')
          },
          onError: (error) => {
            console.error('Streaming error:', error)
            setStreamingMessage(null) // Clear streaming message on error
            toast.error(`Failed to send message: ${error.message}`)
          },
          onAgentTask: (taskId, status, progress) => {
            setAgentEvents((prev) => {
              const idx = prev.findIndex((e) => e.id === taskId)
              if (idx >= 0) {
                const next = [...prev]
                next[idx] = { ...next[idx], status: status as any, progress }
                return next
              }
              return [...prev, { id: taskId, status: status as any, progress }]
            })
          }
        })
        // Provide a cancel hook
        abortRef.current = () => {
          streamingService.cancelRequest()
          setStreamingMessage(null)
          toast.message('Streaming cancelled')
        }
        await abortable
      } else {
        // Use simple API call
        const response = await apiClient.postChat(chatRequest)
        if (response.success) {
          toast.success('Message sent successfully')
        } else {
          throw new Error(response.error || 'Failed to send message')
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error)
      toast.error(`Failed to send message: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }, [chatInput, currentConversation, selectedAgent, isStreaming, featureFlags.streaming, setChatInput, setMessages, setStreamingMessage])

  // Emit typing events (debounced stop)
  const emitTyping = useCallback(() => {
    const conversationId = currentConversation?.id
    if (!conversationId || !realtimeRef.current) return
    realtimeRef.current.emitTyping(conversationId, true)
    if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current)
    typingTimeoutRef.current = setTimeout(() => {
      realtimeRef.current?.emitTyping(conversationId, false)
    }, 1500)
  }, [currentConversation?.id])

  // Message actions
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null)
  const [editingContent, setEditingContent] = useState<string>('')

  const beginEditMessage = useCallback((msgId: string, content: string) => {
    setEditingMessageId(msgId)
    setEditingContent(content)
  }, [])

  const saveEditMessage = useCallback(async () => {
    if (!editingMessageId || !currentConversation?.id) return
    try {
      const res = await apiClient.editMessage(currentConversation.id, editingMessageId, editingContent)
      if (res.success && res.data) {
        setMessages((prev) => prev.map(m => m.id === editingMessageId ? { ...m, content: res.data.content, isEdited: true, updatedAt: new Date().toISOString() } : m))
        toast.success('Message edited')
      } else {
        throw new Error(res.error || 'Edit failed')
      }
    } catch (e) {
      console.error(e)
      toast.error('Failed to edit message')
    } finally {
      setEditingMessageId(null)
      setEditingContent('')
    }
  }, [currentConversation?.id, editingMessageId, editingContent, setMessages])

  const deleteMessageById = useCallback(async (msgId: string) => {
    if (!currentConversation?.id) return
    try {
      const res = await apiClient.deleteMessage(currentConversation.id, msgId)
      if (res.success) {
        setMessages((prev) => prev.filter(m => m.id !== msgId))
        toast.success('Message deleted')
      } else {
        throw new Error(res.error || 'Delete failed')
      }
    } catch (e) {
      console.error(e)
      toast.error('Failed to delete message')
    }
  }, [currentConversation?.id, setMessages])

  const regenerateFromMessage = useCallback(async (msgId: string) => {
    const msg = messages.find(m => m.id === msgId)
    if (!msg) return
    let toSend = ''
    if (msg.role === 'user') {
      toSend = msg.content
    } else {
      // find previous user message
      const idx = messages.findIndex(m => m.id === msgId)
      const prior = [...messages].slice(0, idx).reverse().find(m => m.role === 'user')
      toSend = prior?.content || ''
    }
    if (toSend) {
      await handleSendMessage(toSend)
    }
  }, [messages, setChatInput, handleSendMessage])

  // Conversation actions
  const togglePinConversation = useCallback(async (convId: string) => {
    try {
      const res = await apiClient.pinConversation(convId)
      if (res.success && res.data) {
        setConversations((prev) => prev.map(c => c.id === convId ? { ...c, isPinned: res.data.isPinned } : c))
      } else {
        throw new Error(res.error || 'Pin toggle failed')
      }
    } catch (e) {
      console.error(e)
      toast.error('Failed to toggle pin')
    }
  }, [setConversations])

  const archiveConversationById = useCallback(async (convId: string, archive = true) => {
    try {
      let res
      if (archive) {
        res = await apiClient.archiveConversation(convId)
      } else {
        // Unarchive via update endpoint
        res = await apiClient.updateConversation(convId, { isArchived: false })
      }
      if (res.success && res.data) {
        setConversations((prev) => prev.map(c => c.id === convId ? { ...c, isArchived: res.data.isArchived } : c))
      } else {
        throw new Error(res.error || 'Archive action failed')
      }
    } catch (e) {
      console.error(e)
      toast.error('Failed to update archive state')
    }
  }, [setConversations])

  const deleteConversationById = useCallback(async (convId: string) => {
    try {
      const res = await apiClient.deleteConversation(convId)
      if (res.success) {
        setConversations((prev) => prev.filter(c => c.id !== convId))
        if (currentConversation?.id === convId && conversations[0]) {
          setCurrentConversationId(conversations[0].id)
        }
        toast.success('Conversation deleted')
      } else {
        throw new Error(res.error || 'Delete failed')
      }
    } catch (e) {
      console.error(e)
      toast.error('Failed to delete conversation')
    }
  }, [setConversations, currentConversation?.id, conversations, setCurrentConversationId])

  // Handle creating new conversation
  const handleNewConversation = useCallback(async () => {
    try {
      const response = await apiClient.createConversation({
        title: 'New Conversation',
        agentId: selectedAgent?.id
      })
      
      if (response.success) {
        toast.success('New conversation created')
      }
    } catch (error) {
      console.error('Failed to create conversation:', error)
      toast.error('Failed to create new conversation')
    }
  }, [selectedAgent])

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl/Cmd + Enter to send
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        void handleSendMessage()
      }

      // Ctrl/Cmd + N for new conversation
      if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault()
        void handleNewConversation()
      }

      // Ctrl/Cmd + K for search
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        setShowSearch(true)
      }

      // Escape to close modals
      if (e.key === 'Escape') {
        setShowSearch(false)
        setShowSettings(false)
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [handleSendMessage, handleNewConversation])

  // Handle file upload
  const handleFileUpload = useCallback((files: File[]) => {
    console.log('Files uploaded:', files)
    toast.success(`${files.length} file(s) uploaded`)
  }, [])

  // Handle voice recording
  const handleVoiceToggle = useCallback(() => {
    setVoiceState(prev => ({
      ...prev,
      isRecording: !prev.isRecording
    }))
  }, [])

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-gray-900 via-gray-800 to-black">
      {/* Header Bar */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700 bg-gray-800/50 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setSidebarOpen(true)}
            aria-label="Open sidebar"
            title="Open sidebar"
            className="md:hidden h-9 w-9 p-0 bg-transparent hover:bg-gray-600 rounded-md flex items-center justify-center text-white"
          >
            <Menu className="h-4 w-4" />
          </button>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-r from-purple-600 to-blue-600 rounded-lg flex items-center justify-center">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <span className="text-lg font-semibold text-white">
              Cartrita AI OS
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {isStreaming && (
            <div className="flex items-center gap-2 text-blue-400">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">Processing...</span>
            </div>
          )}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                aria-label="More options"
                title="More options"
                className="h-9 w-9 p-0 bg-transparent hover:bg-gray-600 rounded-md flex items-center justify-center text-white"
              >
                <MoreVertical className="h-4 w-4" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem onClick={() => setShowSearch(true)}>
                <Search className="h-4 w-4 mr-2" />
                Search
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setShowSettings(true)}>
                <Settings className="h-4 w-4 mr-2" />
                Settings
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <AnimatePresence>
          {sidebarOpen && (
            <motion.div
              initial={{ x: -320 }}
              animate={{ x: 0 }}
              exit={{ x: -320 }}
              transition={{ type: 'tween', duration: 0.3 }}
              className="fixed left-0 top-0 z-40 h-full w-80 bg-gray-800 border-r border-gray-700 flex flex-col text-white md:relative md:translate-x-0"
            >
              {/* Sidebar Header */}
              <div className="p-4 border-b border-gray-700">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold">Conversations</h2>
                  <button
                    onClick={() => setSidebarOpen(false)}
                    aria-label="Close sidebar"
                    title="Close sidebar"
                    className="md:hidden h-8 w-8 p-0 bg-transparent hover:bg-gray-600 rounded-md flex items-center justify-center"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </div>

              {/* New Chat Button */}
              <div className="p-4">
                <button
                  onClick={handleNewConversation}
                  className="w-full flex items-center gap-3 h-12 px-4 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 rounded-lg transition-all duration-200 font-medium"
                >
                  <Plus className="h-5 w-5" />
                  New Chat
                </button>
              </div>

              {/* Conversations List */}
              <ScrollArea className="flex-1 px-4">
                <div className="space-y-2">
                  {conversations.map((conv) => (
                    <div
                      key={conv.id}
                      className={cn(
                        "flex items-center gap-3 p-3 rounded-lg hover:bg-gray-700 cursor-pointer transition-colors",
                        currentConversation?.id === conv.id && "bg-gray-700"
                      )}
                      onClick={() => setCurrentConversationId(conv.id)}
                    >
                      <MessageSquare className="h-4 w-4 text-gray-400 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm truncate">{conv.title || 'Untitled'}</p>
                        <p className="text-xs text-gray-400">
                          {new Date(conv.updatedAt).toLocaleDateString()}
                        </p>
                      </div>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <button
                            aria-label="Conversation actions"
                            className="h-8 w-8 rounded hover:bg-gray-600 flex items-center justify-center"
                            onClick={(e) => { e.stopPropagation() }}
                          >
                            <MoreVertical className="h-4 w-4" />
                          </button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent>
                          <DropdownMenuItem onClick={(e) => { e.stopPropagation(); togglePinConversation(conv.id) }}>
                            {conv.isPinned ? 'Unpin' : 'Pin'}
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={(e) => { e.stopPropagation(); archiveConversationById(conv.id, !conv.isArchived) }}>
                            {conv.isArchived ? 'Unarchive' : 'Archive'}
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={(e) => { e.stopPropagation(); deleteConversationById(conv.id) }}>
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  ))}
                </div>
              </ScrollArea>

              {/* Agent Selector */}
              <div className="p-4 border-t border-gray-700">
                <div className="flex items-center gap-3 p-3 rounded-lg bg-gray-700">
                  <Bot className="h-4 w-4 text-blue-400" />
                  <div>
                    <p className="text-sm font-medium">{selectedAgent?.name || 'Cartrita'}</p>
                    <p className="text-xs text-gray-400">
                      {selectedAgent?.description || 'AI Assistant'}
                    </p>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main Chat Interface */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Messages Area */}
          <div className="flex-1 p-6 overflow-hidden">
            <div className="h-full max-w-4xl mx-auto">
              {messages.length === 0 && !streamingMessage ? (
                <div className="text-center py-12">
                  <Bot className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                  <h2 className="text-xl font-semibold mb-2 text-white">How can I help you today?</h2>
                  <p className="text-gray-300">Start a conversation with {selectedAgent?.name || 'an AI agent'}</p>
                </div>
              ) : (
                <MessageList
                  messages={[...messages, ...(streamingMessage ? [{ id: streamingMessage.id, role: streamingMessage.role as any, content: streamingMessage.content }] : [])] as MLMessage[]}
                  fontSize={settings.fontSize as any}
                  autoScroll={settings.autoScroll}
                  highlightCode={!settings.reducedMotion}
                  renderMessage={(message) => (
                    <div
                      className={cn(
                        'flex gap-4 max-w-4xl my-3',
                        message.role === 'user' ? 'justify-end' : 'justify-start'
                      )}
                    >
                      {message.role !== 'user' && (
                        <Avatar className="h-8 w-8 flex-shrink-0">
                          <AvatarFallback className="bg-gradient-to-r from-purple-600 to-blue-600">
                            <Bot className="h-4 w-4 text-white" />
                          </AvatarFallback>
                        </Avatar>
                      )}
                      <div
                        className={cn(
                          'max-w-[80%] rounded-xl px-4 py-3',
                          message.role === 'user'
                            ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white ml-auto'
                            : 'bg-gray-800/50 border border-gray-700 text-white'
                        )}
                      >
                        {editingMessageId === (message as any).id ? (
                          <div className="space-y-2">
                            <Textarea
                              value={editingContent}
                              onChange={(e) => setEditingContent(e.target.value)}
                              className="w-full min-h-[80px]"
                            />
                            <div className="flex gap-2 justify-end">
                              <Button
                                variant="secondary"
                                onClick={() => {
                                  setEditingMessageId(null)
                                  setEditingContent('')
                                }}
                              >
                                Cancel
                              </Button>
                              <Button onClick={saveEditMessage}>Save</Button>
                            </div>
                          </div>
                        ) : (
                          <div className="prose prose-sm dark:prose-invert max-w-none" aria-live={message.id === streamingMessage?.id ? 'polite' : undefined}>
                            {(message as any).content}{message.id === streamingMessage?.id && isStreaming && (
                              <span className="inline-block w-2 h-4 ml-0.5 align-baseline bg-gradient-to-b from-purple-400 to-blue-500 animate-pulse" />
                            )}
                          </div>
                        )}
                        <div className="flex items-center gap-2 mt-2 opacity-75 text-xs">
                          {(message as any).isEdited && <Badge variant="secondary">edited</Badge>}
                        </div>
                        <div className="mt-2 flex justify-end">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <button
                                aria-label="Message actions"
                                className="h-7 w-7 rounded hover:bg-gray-700 flex items-center justify-center"
                              >
                                <MoreVertical className="h-4 w-4" />
                              </button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent>
                              {message.role === 'user' && (
                                <DropdownMenuItem onClick={() => beginEditMessage((message as any).id, (message as any).content)}>
                                  Edit
                                </DropdownMenuItem>
                              )}
                              <DropdownMenuItem onClick={() => regenerateFromMessage((message as any).id)}>
                                Regenerate
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => deleteMessageById((message as any).id)}>
                                Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </div>
                      {message.role === 'user' && (
                        <Avatar className="h-8 w-8 flex-shrink-0">
                          <AvatarFallback>{user?.name?.[0] || 'U'}</AvatarFallback>
                        </Avatar>
                      )}
                    </div>
                  )}
                />
              )}
              <AgentTaskTimeline events={agentEvents} />
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Input Area */}
          <div className="p-6 border-t border-gray-700 bg-gray-900/50 backdrop-blur-sm">
            <div className="max-w-4xl mx-auto">
              {/* Typing indicator */}
              {Object.values(typingUsers).some(Boolean) && (
                <div className="mb-2 text-sm text-blue-300 flex items-center gap-2">
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  Someone is typing…
                </div>
              )}
              {/* Message Input Bar */}
              <div className="flex items-end gap-3 bg-gray-800/50 border border-gray-600 rounded-2xl p-3 focus-within:border-purple-500 transition-colors">
                {/* Attach Files Button */}
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        onClick={() => setShowUploadDialog(true)}
                        disabled={isStreaming}
                        aria-label="Attach files"
                        title="Attach files"
                        className="h-10 w-10 flex-shrink-0 bg-transparent hover:bg-gray-700 rounded-lg disabled:pointer-events-none disabled:opacity-50 flex items-center justify-center text-gray-400 hover:text-white transition-colors"
                      >
                        <Paperclip className="h-5 w-5" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent>Attach files</TooltipContent>
                  </Tooltip>
                </TooltipProvider>

                {/* Text Input */}
                <Textarea
                  ref={inputRef}
                  value={chatInput}
                  onChange={(e) => { setChatInput(e.target.value); emitTyping() }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      void handleSendMessage()
                    }
                  }}
                  placeholder={`Message ${selectedAgent?.name || 'Cartrita'}...`}
                  className="flex-1 min-h-[44px] max-h-32 resize-none border-0 bg-transparent text-white placeholder-gray-400 focus:ring-0 focus:outline-none p-0"
                  disabled={isStreaming}
                />

                {/* Voice Input Button */}
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        onClick={handleVoiceToggle}
                        disabled={isStreaming}
                        aria-pressed={voiceState.isRecording}
                        aria-label={voiceState.isRecording ? 'Stop recording' : 'Start voice input'}
                        title={voiceState.isRecording ? 'Stop recording' : 'Start voice input'}
                        className={cn(
                          "h-10 w-10 flex-shrink-0 rounded-lg disabled:pointer-events-none disabled:opacity-50 flex items-center justify-center transition-colors",
                          voiceState.isRecording
                            ? "bg-red-500 hover:bg-red-600 text-white"
                            : "bg-transparent hover:bg-gray-700 text-gray-400 hover:text-white"
                        )}
                      >
                        {voiceState.isRecording ? (
                          <MicOff className="h-5 w-5" />
                        ) : (
                          <Mic className="h-5 w-5" />
                        )}
                      </button>
                    </TooltipTrigger>
                    <TooltipContent>
                      {voiceState.isRecording ? 'Stop recording' : 'Start voice input'}
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>

                {/* Send Button */}
                {isStreaming && streamingMessage ? (
                  <button
                    onClick={(e) => { e.preventDefault(); abortRef.current?.() }}
                    aria-label="Cancel streaming"
                    title="Cancel streaming"
                    className="h-10 px-3 flex-shrink-0 bg-red-600 hover:bg-red-500 rounded-lg text-white flex items-center justify-center transition-all duration-200"
                  >
                    <X className="h-5 w-5" />
                  </button>
                ) : (
                  <button
                    onClick={(e) => { e.preventDefault(); handleSendMessage(); }}
                    disabled={!chatInput.trim() || !selectedAgent}
                    aria-label="Send message"
                    title="Send message"
                    className="h-10 w-10 flex-shrink-0 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 rounded-lg disabled:pointer-events-none disabled:opacity-50 flex items-center justify-center text-white transition-all duration-200"
                  >
                    <Send className="h-5 w-5" />
                  </button>
                )}
              </div>
            </div>

            {/* Upload Dialog */}
            {showUploadDialog && (
              <Dialog
                open={showUploadDialog}
                onClose={() => { setShowUploadDialog(false); setUploadProgress(0) }}
                title="Upload files"
              >
                <div className="space-y-4">
                  <FileUploader
                    multiple
                    onFiles={async (files) => {
                      if (files.length === 0) return
                      try {
                        const res = await apiClient.uploadMultipleFiles(files, currentConversation?.id, (p) => setUploadProgress(p))
                        if (res.success) {
                          toast.success(`${files.length} file(s) uploaded`)
                          setAttachments((prev) => [
                            ...prev,
                            ...files.map((f, i) => ({
                              id: `${f.name}-${Date.now()}-${i}`,
                              name: f.name,
                              size: f.size,
                              type: f.type
                            }))
                          ])
                          setShowUploadDialog(false)
                        } else {
                          throw new Error(res.error || 'Upload failed')
                        }
                      } catch (e) {
                        console.error(e)
                        toast.error('File upload failed')
                      } finally {
                        setUploadProgress(0)
                      }
                    }}
                  />
                  {uploadProgress > 0 && (
                    <div className="space-y-1">
                      <div className="text-xs text-gray-400">Uploading… {uploadProgress}%</div>
                      <Progress value={uploadProgress} max={100} />
                    </div>
                  )}
                </div>
              </Dialog>
            )}
          </div>
          {/* Attachments Bar */}
          <AttachmentsBar
            items={attachments}
            onRemove={(id) => setAttachments((list) => list.filter((a) => a.id !== id))}
          />
        </div>
      </div>

      {/* Overlay for mobile sidebar */}
      {sidebarOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-30 bg-black/50 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      <SettingsModal open={showSettings} onClose={() => setShowSettings(false)} />
    </div>
  )
}