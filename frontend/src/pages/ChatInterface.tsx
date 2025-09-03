// Cartrita AI OS - Main Chat Interface
// ChatGPT-like interface with enhanced Cartrita AI OS features

'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useAtom, useAtomValue } from 'jotai'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import {
  Send,
  Plus,
  Settings,
  User,
  MessageSquare,
  Search,
  Menu,
  X,
  Mic,
  MicOff,
  Paperclip,
  MoreVertical,
  Edit3,
  Trash2,
  Copy,
  ThumbsUp,
  ThumbsDown,
  RotateCcw,
  Download,
  Share,
  Zap,
  Bot,
  User as UserIcon,
  Clock,
  CheckCircle,
  AlertCircle,
  Loader2
} from 'lucide-react'
import { cn } from '@/utils'
import {
  currentConversationAtom,
  conversationsAtom,
  currentMessagesAtom,
  selectedAgentAtom,
  agentsAtom,
  sidebarOpenAtom,
  chatInputAtom,
  chatInputFocusedAtom,
  isStreamingAtom,
  streamingMessageAtom,
  userAtom,
  themeAtom,
  settingsAtom,
  featureFlagsAtom
} from '@/stores'
import {
  useConversations,
  useCreateConversation,
  // useSendMessage, // Temporarily disabled
  // useStreamMessage, // Temporarily disabled
  useMessages
} from '@/hooks'
import type { Message, Conversation, Agent } from '@/types'

// Components
import {
  Input,
  Textarea,
  ScrollArea,
  Avatar,
  AvatarFallback,
  AvatarImage,
  Badge,
  Separator,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger
} from '@/components/ui'
import { MessageBubble } from '@/components/MessageBubble'
import { AgentSelector } from '@/components/AgentSelector'
import { StreamingIndicator } from '@/components/StreamingIndicator'
import { VoiceInput } from '@/components/VoiceInput'
import { FileUpload } from '@/components/FileUpload'
import { SearchInterface } from '@/components/SearchInterface'
import { SettingsPanel } from '@/components/SettingsPanel'

// Main Chat Interface Component
export default function ChatInterface() {
  // State
  const [sidebarOpen, setSidebarOpen] = useAtom(sidebarOpenAtom)
  const [chatInput, setChatInput] = useAtom(chatInputAtom)
  const [isInputFocused, setIsInputFocused] = useAtom(chatInputFocusedAtom)
  const [showSearch, setShowSearch] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [isRecording, setIsRecording] = useState(false)

  // Data
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
  const streamingMessage = useAtomValue(streamingMessageAtom)

  // Hooks
  const { data: conversationsData, isLoading: conversationsLoading } = useConversations()
  const { data: messagesData, isLoading: messagesLoading } = useMessages(currentConversation?.id || '')
  const createConversation = useCreateConversation()
  // const sendMessage = useSendMessage() // Temporarily disabled
  // const streamMessage = useStreamMessage() // Temporarily disabled

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (settings.autoScroll && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, streamingMessage, settings.autoScroll])

  // Focus input when conversation changes
  useEffect(() => {
    if (currentConversation && inputRef.current && !isInputFocused) {
      inputRef.current.focus()
    }
  }, [currentConversation?.id, isInputFocused])

  // Handle sending message
  const handleSendMessage = useCallback(async () => {
    if (!chatInput.trim() || !currentConversation || !selectedAgent || isStreaming) return

    const messageContent = chatInput.trim()
    setChatInput('')

    try {
      // Temporarily disabled due to Jotai atom issues
      // if (featureFlags.streaming) {
      //   await streamMessage.mutateAsync({
      //     conversationId: currentConversation.id,
      //     message: {
      //       message: messageContent,
      //       agentOverride: selectedAgent.id,
      //       stream: true
      //     }
      //   })
      // } else {
      //   await sendMessage.mutateAsync({
      //     conversationId: currentConversation.id,
      //     message: {
      //       message: messageContent,
      //       agentOverride: selectedAgent.id,
      //       stream: false
      //     }
      //   })
      // }
      toast.info('Message sending temporarily disabled due to build issues')
    } catch (error) {
      console.error('Failed to send message:', error)
      toast.error('Failed to send message')
    }
  }, [chatInput, currentConversation, selectedAgent, isStreaming, featureFlags.streaming, setChatInput])

  // Handle creating new conversation
  const handleNewConversation = useCallback(() => {
    createConversation.mutate({
      title: 'New Conversation',
      agentId: selectedAgent?.id
    })
  }, [createConversation, selectedAgent])

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl/Cmd + Enter to send
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        handleSendMessage()
      }

      // Ctrl/Cmd + N for new conversation
      if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault()
        handleNewConversation()
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
    // Handle file upload logic here
    console.log('Files uploaded:', files)
    toast.success(`${files.length} file(s) uploaded`)
  }, [])

  // Handle voice input
  const handleVoiceInput = useCallback((transcript: string) => {
    setChatInput(prev => prev + (prev ? ' ' : '') + transcript)
    setIsRecording(false)
    toast.success('Voice input added')
  }, [setChatInput])

  // Render sidebar
  const renderSidebar = () => (
    <motion.div
      initial={{ x: -300 }}
      animate={{ x: sidebarOpen ? 0 : -300 }}
      transition={{ type: 'tween', duration: 0.3 }}
      className={cn(
        'fixed left-0 top-0 z-40 h-full w-80 bg-background border-r border-border',
        'flex flex-col'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="flex items-center gap-3">
          <Avatar className="h-8 w-8">
            <AvatarImage src={user?.avatar} />
            <AvatarFallback>
              <User className="h-4 w-4" />
            </AvatarFallback>
          </Avatar>
          <div>
            <p className="text-sm font-medium">{user?.name || 'User'}</p>
            <p className="text-xs text-muted-foreground">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={() => setSidebarOpen(false)}
          className="md:hidden h-9 px-3 bg-transparent hover:bg-accent hover:text-accent-foreground rounded-md"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* New Chat Button */}
      <div className="p-4">
        <button
          onClick={handleNewConversation}
          className="w-full justify-start gap-2 h-10 px-4 py-2 bg-primary text-primary-foreground hover:bg-primary/90 rounded-md disabled:pointer-events-none disabled:opacity-50"
          disabled={createConversation.isPending}
        >
          <Plus className="h-4 w-4" />
          New Chat
          {createConversation.isPending && <Loader2 className="h-4 w-4 animate-spin ml-auto" />}
        </button>
      </div>

      {/* Conversations List */}
      <ScrollArea className="flex-1 px-2">
        <div className="space-y-1">
          {conversationsLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="h-12 bg-muted rounded-lg animate-pulse" />
              ))}
            </div>
          ) : (
            conversations.map((conversation) => (
              <motion.div
                key={conversation.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={cn(
                  'group flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors',
                  'hover:bg-muted',
                  currentConversation?.id === conversation.id && 'bg-muted'
                )}
                onClick={() => {
                  // Set current conversation
                  console.log('Switch to conversation:', conversation.id)
                }}
              >
                <MessageSquare className="h-4 w-4 text-muted-foreground" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">
                    {conversation.title || 'Untitled'}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {conversation.metadata?.lastActivity
                      ? new Date(conversation.metadata.lastActivity).toLocaleDateString()
                      : 'No messages'
                    }
                  </p>
                </div>
              </motion.div>
            ))
          )}
        </div>
      </ScrollArea>

      {/* Agent Selector */}
      <div className="p-4 border-t border-border">
        <AgentSelector />
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-border">
        <div className="flex items-center justify-between">
          <button
            onClick={() => setShowSettings(true)}
            className="h-9 px-3 bg-transparent hover:bg-accent hover:text-accent-foreground rounded-md"
          >
            <Settings className="h-4 w-4" />
          </button>
          <button
            onClick={() => setShowSearch(true)}
            className="h-9 px-3 bg-transparent hover:bg-accent hover:text-accent-foreground rounded-md"
          >
            <Search className="h-4 w-4" />
          </button>
        </div>
      </div>
    </motion.div>
  )

  // Render main chat area
  const renderChatArea = () => (
    <div className="flex-1 flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setSidebarOpen(true)}
            className="md:hidden h-9 px-3 bg-transparent hover:bg-accent hover:text-accent-foreground rounded-md"
          >
            <Menu className="h-4 w-4" />
          </button>
          <div>
            <h1 className="text-lg font-semibold">
              {currentConversation?.title || 'New Chat'}
            </h1>
            {selectedAgent && (
              <p className="text-sm text-muted-foreground flex items-center gap-2">
                <Bot className="h-4 w-4" />
                {selectedAgent.name}
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {isStreaming && <StreamingIndicator />}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="h-9 px-3 bg-transparent hover:bg-accent hover:text-accent-foreground rounded-md">
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

      {/* Messages */}
      <ScrollArea className="flex-1 p-4">
        <div className="max-w-4xl mx-auto space-y-6">
          {messagesLoading ? (
            <div className="space-y-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className={cn('flex gap-3', i % 2 === 0 ? 'justify-end' : 'justify-start')}>
                  <div className="max-w-[80%] space-y-2">
                    <div className="h-4 bg-muted rounded animate-pulse" />
                    <div className="h-4 bg-muted rounded w-3/4 animate-pulse" />
                  </div>
                </div>
              ))}
            </div>
          ) : messages.length === 0 && !streamingMessage ? (
            <div className="text-center py-12">
              <Bot className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h2 className="text-xl font-semibold mb-2">How can I help you today?</h2>
              <p className="text-muted-foreground">
                Start a conversation with {selectedAgent?.name || 'an AI agent'}
              </p>
            </div>
          ) : (
            <>
              <AnimatePresence>
                {messages.map((message) => (
                  <MessageBubble
                    key={message.id}
                    message={message}
                    isUser={message.role === 'user'}
                  />
                ))}
              </AnimatePresence>

              {/* Streaming message */}
              {streamingMessage && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex gap-3 justify-start"
                >
                  <Avatar className="h-8 w-8">
                    <AvatarFallback>
                      <Bot className="h-4 w-4" />
                    </AvatarFallback>
                  </Avatar>
                  <div className="max-w-[80%]">
                    <div className="bg-muted rounded-lg p-4">
                      <div className="prose prose-sm dark:prose-invert max-w-none">
                        {streamingMessage.content}
                        <span className="animate-pulse">|</span>
                      </div>
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
      <div className="p-4 border-t border-border">
        <div className="max-w-4xl mx-auto">
          <div className="relative">
            <Textarea
              ref={inputRef}
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onFocus={() => setIsInputFocused(true)}
              onBlur={() => setIsInputFocused(false)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSendMessage()
                }
              }}
              placeholder={`Message ${selectedAgent?.name || 'AI agent'}...`}
              className="min-h-[60px] max-h-32 resize-none pr-24"
              disabled={isStreaming}
            />

            {/* Action Buttons */}
            <div className="absolute right-2 bottom-2 flex items-center gap-1">
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      disabled={isStreaming}
                      className="h-8 w-8 p-0 bg-transparent hover:bg-accent hover:text-accent-foreground rounded disabled:pointer-events-none disabled:opacity-50"
                    >
                      <Paperclip className="h-4 w-4" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>Attach files</TooltipContent>
                </Tooltip>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      onClick={() => setIsRecording(!isRecording)}
                      disabled={isStreaming}
                      className={cn("h-8 w-8 p-0 bg-transparent hover:bg-accent hover:text-accent-foreground rounded disabled:pointer-events-none disabled:opacity-50", isRecording && 'text-red-500')}
                    >
                      {isRecording ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>Voice input</TooltipContent>
                </Tooltip>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      onClick={handleSendMessage}
                      disabled={!chatInput.trim() || !currentConversation || !selectedAgent || isStreaming}
                      className="ml-1 h-8 w-8 p-0 bg-primary text-primary-foreground hover:bg-primary/90 rounded disabled:pointer-events-none disabled:opacity-50"
                    >
                      {isStreaming ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Send className="h-4 w-4" />
                      )}
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>Send message (Ctrl+Enter)</TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
          </div>

          {/* Hidden file input */}
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            onChange={(e) => {
              const files = Array.from(e.target.files || [])
              if (files.length > 0) {
                handleFileUpload(files)
              }
            }}
          />

          {/* Voice input component */}
          {isRecording && (
            <VoiceInput
              onTranscript={handleVoiceInput}
              onCancel={() => setIsRecording(false)}
            />
          )}

          {/* File upload component */}
          <FileUpload
            onFilesSelected={handleFileUpload}
            disabled={isStreaming}
          />
        </div>
      </div>
    </div>
  )

  return (
    <div className="h-screen flex bg-background">
      {/* Sidebar */}
      {renderSidebar()}

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {renderChatArea()}
      </div>

      {/* Modals */}
      <AnimatePresence>
        {showSearch && (
          <SearchInterface isOpen={showSearch} onClose={() => setShowSearch(false)} />
        )}
        {showSettings && (
          <SettingsPanel isOpen={showSettings} onClose={() => setShowSettings(false)} />
        )}
      </AnimatePresence>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-30 bg-black/50 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  )
}