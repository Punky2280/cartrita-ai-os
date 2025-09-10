// Cartrita AI OS - Modern Chat Interface
// Redesigned ChatGPT-like interface with proper architecture

import { useState, useEffect, useRef, useCallback } from 'react'
import { useAtom, useAtomValue, useSetAtom } from 'jotai'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
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
  TooltipTrigger
} from '@/components/ui'

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
  const [showSettings, setShowSettings] = useState(false)
  const [showSearch, setShowSearch] = useState(false)
  const [voiceState, setVoiceState] = useState<VoiceState>({
    isRecording: false,
    isProcessing: false,
    currentTranscription: '',
    audioLevel: 0
  })

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

  // Focus input when conversation changes
  useEffect(() => {
    if (currentConversation && inputRef.current) {
      inputRef.current.focus()
    }
  }, [currentConversation?.id])

  // Handle sending message
  const handleSendMessage = useCallback(async () => {
    if (!chatInput.trim() || !selectedAgent || isStreaming) return

    const messageContent = chatInput.trim()
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
        await streamingService.streamChat(chatRequest, {
          onChunk: (chunk) => {
            console.log('Streaming chunk:', chunk.content)
            // Update streaming message with new content using callback to avoid closure issues
            setStreamingMessage(prev => {
              if (prev) {
                return {
                  ...prev,
                  content: prev.content + chunk.content,
                  updatedAt: new Date().toISOString()
                }
              }
              return prev
            })
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
            if (status === 'started') {
              toast.info(`Agent task started: ${taskId}`)
            } else if (status === 'completed') {
              toast.success(`Agent task completed: ${taskId}`)
            } else if (status === 'failed') {
              toast.error(`Agent task failed: ${taskId}`)
            }
          }
        })
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
  }, [chatInput, currentConversation, selectedAgent, isStreaming, featureFlags.streaming, setChatInput, setMessages, setStreamingMessage, streamingMessage])

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
            onClick={() => { { setSidebarOpen(true);; }}}
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
              <button className="h-9 w-9 p-0 bg-transparent hover:bg-gray-600 rounded-md flex items-center justify-center text-white">
                <MoreVertical className="h-4 w-4" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem onClick={() => { { setShowSearch(true);; }}}>
                <Search className="h-4 w-4 mr-2" />
                Search
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => { { setShowSettings(true);; }}}>
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
                    onClick={() => { { setSidebarOpen(false);; }}}
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
                    >
                      <MessageSquare className="h-4 w-4 text-gray-400 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm truncate">{conv.title || 'Untitled'}</p>
                        <p className="text-xs text-gray-400">
                          {new Date(conv.updatedAt).toLocaleDateString()}
                        </p>
                      </div>
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
          <ScrollArea className="flex-1 p-6">
            <div className="max-w-4xl mx-auto space-y-6">
              {messages.length === 0 && !streamingMessage ? (
                <div className="text-center py-12">
                  <Bot className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                  <h2 className="text-xl font-semibold mb-2 text-white">
                    How can I help you today?
                  </h2>
                  <p className="text-gray-300">
                    Start a conversation with {selectedAgent?.name || 'an AI agent'}
                  </p>
                </div>
              ) : (
                <>
                  {messages.map((message) => (
                    <motion.div
                      key={message.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={cn(
                        "flex gap-4 max-w-4xl",
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

                      <div className={cn(
                        "max-w-[80%] rounded-xl px-4 py-3",
                        message.role === 'user'
                          ? "bg-gradient-to-r from-purple-600 to-blue-600 text-white ml-auto"
                          : "bg-gray-800/50 border border-gray-700 text-white"
                      )}>
                        <div className="prose prose-sm dark:prose-invert max-w-none">
                          {message.content}
                        </div>
                      </div>

                      {message.role === 'user' && (
                        <Avatar className="h-8 w-8 flex-shrink-0">
                          <AvatarFallback>
                            {user?.name?.[0] || 'U'}
                          </AvatarFallback>
                        </Avatar>
                      )}
                    </motion.div>
                  ))}

                  {/* Streaming message */}
                  {streamingMessage && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex gap-4 justify-start max-w-4xl"
                    >
                      <Avatar className="h-8 w-8 flex-shrink-0">
                        <AvatarFallback className="bg-gradient-to-r from-purple-600 to-blue-600">
                          <Bot className="h-4 w-4 text-white" />
                        </AvatarFallback>
                      </Avatar>
                      <div className="max-w-[80%] rounded-xl px-4 py-3 bg-gray-800/50 border border-gray-700 text-white">
                        <div className="prose prose-sm dark:prose-invert max-w-none">
                          {streamingMessage.content}
                          <span className="animate-pulse">|</span>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </>
              )}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>

          {/* Input Area */}
          <div className="p-6 border-t border-gray-700 bg-gray-900/50 backdrop-blur-sm">
            <div className="max-w-4xl mx-auto">
              {/* Message Input Bar */}
              <div className="flex items-end gap-3 bg-gray-800/50 border border-gray-600 rounded-2xl p-3 focus-within:border-purple-500 transition-colors">
                {/* Attach Files Button */}
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        onClick={() => { { fileInputRef.current?.click();; }}}
                        disabled={isStreaming}
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
                  onChange={(e) => { { setChatInput(e.target.value); ; }}}
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
                <button
                  onClick={handleSendMessage}
                  disabled={!chatInput.trim() || !selectedAgent || isStreaming}
                  className="h-10 w-10 flex-shrink-0 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 rounded-lg disabled:pointer-events-none disabled:opacity-50 flex items-center justify-center text-white transition-all duration-200"
                >
                  {isStreaming ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    <Send className="h-5 w-5" />
                  )}
                </button>
              </div>
            </div>

            {/* Hidden file input */}
            <input
              ref={fileInputRef}
              type="file"
              multiple
              className="hidden"
              onChange={(e) => { { {
                const files = Array.from(e.target.files || [])
                if (files.length > 0) {
                  handleFileUpload(files)
                ; ; }}}
              }}
            />
          </div>
        </div>
      </div>

      {/* Overlay for mobile sidebar */}
      {sidebarOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-30 bg-black/50 md:hidden"
          onClick={() => { { setSidebarOpen(false);; }}}
        />
      )}
    </div>
  )
}