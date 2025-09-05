// Cartrita AI OS - Main Chat Interface
// ChatGPT-like interface with enhanced Cartrita AI OS features

'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useAtom, useAtomValue } from 'jotai'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import { useVoice } from '@/hooks/useVoice'
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
  Volume2
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
  useMessages
} from '@/hooks'
import { useSSEChat, useStreamingChat } from '@/hooks/useSSEChat'
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
import { VoiceOutput } from '@/components/VoiceOutput'
import { FileUpload } from '@/components/FileUpload'
import { SearchInterface } from '@/components/SearchInterface'
import { SettingsPanel } from '@/components/SettingsPanel'
import AudioAnalyticsSidebar from '@/components/AudioAnalyticsSidebar'
import HeaderBar from '@/components/ui/HeaderBar'
import Sidebar from '@/components/ui/Sidebar'
import StatusBar from '@/components/ui/StatusBar'

// Main Chat Interface Component
export default function ChatInterface() {
  // State
  const [sidebarOpen, setSidebarOpen] = useAtom(sidebarOpenAtom)
  const [chatInput, setChatInput] = useAtom(chatInputAtom)
  const [isInputFocused, setIsInputFocused] = useAtom(chatInputFocusedAtom)
  const [showSearch, setShowSearch] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [showAudioAnalytics, setShowAudioAnalytics] = useState(false)
  const [voiceOutputMode, setVoiceOutputMode] = useState(false)

  // Voice functionality - Real Deepgram integration
  const voice = useVoice({
    enableAnalytics: true,
    enableMetrics: true,
    onTranscription: (transcription) => {
      if (transcription.is_final && transcription.text.trim()) {
        setChatInput(prev => prev + ' ' + transcription.text)
      }
    },
    onResponse: (response) => {
      // Handle AI voice response
      toast.success('Voice response received')
    },
    onError: (error) => {
      toast.error('Voice error: ' + error.message)
    }
  })

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
  
  // SSE Chat hooks
  const streamingChat = useStreamingChat()
  const simpleChat = useSSEChat({
    enableStreaming: false,
    onComplete: (response) => {
      console.log('Chat response received:', response)
      toast.success('Message sent successfully')
    },
    onError: (error) => {
      console.error('Chat error:', error)
      toast.error('Failed to send message: ' + error.message)
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
    if (!chatInput.trim() || !selectedAgent || isStreaming) return

    const messageContent = chatInput.trim()
    setChatInput('')

    const chatRequest = {
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

    try {
      if (featureFlags.streaming) {
        // Use streaming chat
        await streamingChat.sendMessage(chatRequest)
      } else {
        // Use simple non-streaming chat
        await simpleChat.sendMessageNonStreaming(chatRequest)
      }
    } catch (error) {
      console.error('Failed to send message:', error)
      // Error is handled by the hook's onError callback
    }
  }, [chatInput, currentConversation, selectedAgent, isStreaming, featureFlags.streaming, setChatInput, streamingChat, simpleChat])

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

      // Ctrl/Cmd + A for audio analytics
      if ((e.ctrlKey || e.metaKey) && e.key === 'a') {
        e.preventDefault()
        setShowAudioAnalytics(!showAudioAnalytics)
      }

      // Escape to close modals
      if (e.key === 'Escape') {
        setShowSearch(false)
        setShowSettings(false)
        setShowAudioAnalytics(false)
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [handleSendMessage, handleNewConversation, showAudioAnalytics])

  // Handle file upload
  const handleFileUpload = useCallback((files: File[]) => {
    // Handle file upload logic here
    console.log('Files uploaded:', files)
    toast.success(`${files.length} file(s) uploaded`)
  }, [])

  // Handle voice input
  const handleVoiceInput = useCallback(async (transcript: string) => {
    if (!transcript.trim()) {
      toast.error('No speech detected')
      return
    }

    try {
      // Stop recording
      voice.stopRecording()

      // Show processing state
      toast.info('Processing voice conversation...')

      // Prepare conversation history for context
      const conversationHistory = messages.map(msg => ({
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp
      }))

      // Send voice conversation request
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/chat/voice`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          conversationId: currentConversation?.id || 'voice-conversation',
          transcribedText: transcript,
          conversationHistory: conversationHistory,
          voiceMode: true
        })
      })

      if (!response.ok) {
        throw new Error('Voice conversation failed')
      }

      const result = await response.json()

      // Handle voice output if enabled
      if (voiceOutputMode && result.response) {
        voice.speak(result.response)
      }

      // Add AI response to conversation
      if (result.response) {
        // This would be handled by the chat system
        toast.success('Voice conversation completed')
      }

    } catch (error) {
      console.error('Voice conversation error:', error)
      toast.error('Voice conversation failed: ' + (error as Error).message)
    }
  }, [voice, messages, currentConversation, voiceOutputMode])



  return (
    <div className="h-screen flex flex-col bg-chatgpt-grey">
      {/* Header Bar */}
      <HeaderBar />

      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <Sidebar
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
          onNewChat={handleNewConversation}
          conversations={conversations}
          selectedAgent={selectedAgent}
          onAgentSelect={() => {}} // TODO: Implement agent selection
          onSettings={() => setShowSettings(true)}
          onSearch={() => setShowSearch(true)}
        />

        {/* Main Chat Interface */}
        <div className="flex-1 flex flex-col bg-chatgpt-grey">
          {/* Chat Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-600 bg-chatgpt-grey-light">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setSidebarOpen(true)}
                className="md:hidden h-9 w-9 p-0 bg-transparent hover:bg-gray-600 rounded-md flex items-center justify-center text-white"
              >
                <Menu className="h-4 w-4" />
              </button>
              <div>
                <h1 className="text-lg font-semibold text-white">
                  {currentConversation?.title || 'New Chat'}
                </h1>
                {selectedAgent && (
                  <p className="text-sm text-gray-300 flex items-center gap-2">
                    <Bot className="h-4 w-4" />
                    {selectedAgent.name}
                  </p>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              {isStreaming && <StreamingIndicator />}
              <button
                onClick={() => setShowAudioAnalytics(!showAudioAnalytics)}
                className={cn(
                  "h-9 w-9 p-0 rounded-md flex items-center justify-center text-white transition-colors",
                  showAudioAnalytics
                    ? "bg-cartrita-blue hover:bg-cartrita-blue-light"
                    : "bg-transparent hover:bg-gray-600"
                )}
                title="Audio Analytics (Ctrl+A)"
              >
                <BarChart3 className="h-4 w-4" />
              </button>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button className="h-9 w-9 p-0 bg-transparent hover:bg-gray-600 rounded-md flex items-center justify-center text-white">
                    <MoreVertical className="h-4 w-4" />
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent>
                  <DropdownMenuItem onClick={() => setShowSearch(true)}>
                    <Search className="h-4 w-4 mr-2" />
                    Search
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setShowAudioAnalytics(!showAudioAnalytics)}>
                    <BarChart3 className="h-4 w-4 mr-2" />
                    Audio Analytics
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setShowSettings(true)}>
                    <Settings className="h-4 w-4 mr-2" />
                    Settings
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>

          {/* Messages Area with Audio Analytics Sidebar */}
          <div className="flex flex-1 overflow-hidden">
            <div className="flex-1 flex flex-col">
              {/* Messages Area */}
              <ScrollArea className="flex-1 p-4 bg-chatgpt-grey">
                <div className="max-w-4xl mx-auto space-y-6">
                  {messagesLoading ? (
                    <div className="space-y-4">
                      {Array.from({ length: 3 }).map((_, i) => (
                        <div key={i} className={cn('flex gap-3', i % 2 === 0 ? 'justify-end' : 'justify-start')}>
                          <div className="max-w-[80%] space-y-2">
                            <div className="h-4 bg-chatgpt-grey-light rounded animate-pulse" />
                            <div className="h-4 bg-chatgpt-grey-light rounded w-3/4 animate-pulse" />
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : messages.length === 0 && !streamingMessage ? (
                    <div className="text-center py-12">
                      <Bot className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                      <h2 className="text-xl font-semibold mb-2 text-white">How can I help you today?</h2>
                      <p className="text-gray-300">
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
                            <AvatarFallback className="bg-cartrita-blue">
                              <Bot className="h-4 w-4" />
                            </AvatarFallback>
                          </Avatar>
                          <div className="max-w-[80%]">
                            <div className="glassmorphism rounded-lg p-4 text-white">
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

              {/* Multi-Modal Input Area */}
              <div className="p-4 border-t border-gray-600 bg-chatgpt-grey-light">
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
                      className="min-h-[60px] max-h-32 resize-none pr-24 bg-chatgpt-grey-dark border-gray-600 text-white placeholder-gray-400 focus:border-cartrita-blue"
                      disabled={isStreaming}
                    />

                    {/* Action Buttons */}
                    <div className="absolute right-2 bottom-2 flex items-center gap-1">
                      <button
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isStreaming}
                        className="h-9 w-9 p-0 bg-transparent hover:bg-gray-600 rounded-md disabled:pointer-events-none disabled:opacity-50 flex items-center justify-center text-white"
                      >
                        <Paperclip className="h-4 w-4" />
                      </button>

                      <button
                        onClick={voice.toggleRecording}
                        disabled={isStreaming || voice.isProcessing}
                        className={cn(
                          "h-9 w-9 p-0 bg-transparent hover:bg-fuschia-pink rounded-md disabled:pointer-events-none disabled:opacity-50 transition-all flex items-center justify-center",
                          voice.isRecording && 'bg-fuschia-pink animate-pulse-fuschia',
                          voice.isProcessing && 'bg-orange-500',
                          voice.isSpeaking && 'bg-green-500'
                        )}
                      >
                        {voice.isRecording ? (
                          <MicOff className="h-4 w-4" />
                        ) : voice.isProcessing ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Mic className="h-4 w-4" />
                        )}
                      </button>

                      <button
                        onClick={() => setVoiceOutputMode(!voiceOutputMode)}
                        disabled={isStreaming}
                        className={cn(
                          "h-9 w-9 p-0 bg-transparent hover:bg-blue-500 rounded-md disabled:pointer-events-none disabled:opacity-50 transition-all flex items-center justify-center",
                          voiceOutputMode && 'bg-blue-500'
                        )}
                      >
                        <Volume2 className="h-4 w-4" />
                      </button>

                      <button
                        onClick={handleSendMessage}
                        disabled={!chatInput.trim() || !selectedAgent || isStreaming}
                        className="ml-1 h-9 w-9 p-0 bg-cartrita-blue hover:bg-cartrita-blue/80 rounded-md disabled:pointer-events-none disabled:opacity-50 flex items-center justify-center text-white"
                      >
                        {isStreaming ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Send className="h-4 w-4" />
                        )}
                      </button>
                    </div>
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
              {(voice.isRecording || voice.currentTranscription) && (
                <div className="bg-chatgpt-grey border border-gray-600 rounded-lg p-4 mb-4">
                  <div className="flex items-center gap-3">
                    <div className={cn(
                      "h-3 w-3 rounded-full animate-pulse",
                      voice.isRecording ? "bg-fuschia-pink" : "bg-cartrita-blue"
                    )}>
                    </div>
                    <div className="flex-1">
                      <div className="text-sm text-gray-300">
                        {voice.isRecording ? "Listening..." : "Processing..."}
                      </div>
                      {voice.currentTranscription && (
                        <div className="text-white">
                          {voice.currentTranscription}
                        </div>
                      )}
                      {voice.finalTranscription && (
                        <div className="text-white font-medium">
                          {voice.finalTranscription}
                        </div>
                      )}
                    </div>
                    <button
                      onClick={() => voice.stopRecording()}
                      className="text-gray-400 hover:text-white"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>

                  {/* Voice quality indicator */}
                  {voice.isRecording && (
                    <div className="mt-2 flex items-center gap-2">
                      <div className="text-xs text-gray-400">
                        Signal: {voice.signalQuality}
                      </div>
                      <div className="flex-1 bg-chatgpt-grey-dark rounded-full h-1">
                        <div
                          className="bg-cartrita-blue rounded-full h-full transition-all duration-150"
                          style={{ width: `${(voice.audioLevel / 255) * 100}%` }}
                        ></div>
                      </div>
                    </div>
                  )}

                  {/* Voice analytics */}
                  {voice.analytics && (
                    <div className="mt-2 flex items-center gap-4 text-xs text-gray-400">
                      <span>Sentiment: {voice.analytics.sentiment.label}</span>
                      {voice.analytics.language_detected && (
                        <span>Language: {voice.analytics.language_detected}</span>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Voice Output Component */}
              {voiceOutputMode && (
                <div className="mb-4">
                  <VoiceOutput
                    onVoiceStart={() => toast.info('Voice output started')}
                    onVoiceEnd={() => toast.success('Voice output completed')}
                    onError={(error) => toast.error(`Voice error: ${error.message}`)}
                  />
                </div>
              )}

              {/* File upload component */}
              <FileUpload
                onFilesSelected={handleFileUpload}
                disabled={isStreaming}
              />
            </div>

            {/* Audio Analytics Sidebar */}
            <AudioAnalyticsSidebar
              isOpen={showAudioAnalytics}
              onToggle={() => setShowAudioAnalytics(!showAudioAnalytics)}
              messages={messages}
              isStreaming={isStreaming}
            />
          </div>
        </div>
      </div>

      {/* Status Bar */}
      <StatusBar
        currentModel={selectedAgent?.name || 'Cartrita'}
        tokenCount={messages.reduce((acc, msg) => acc + (msg.content?.length || 0), 0) / 4} // Rough token estimate
        voiceActivity={voice.isRecording}
        currentTime={new Date()}
      />

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
    </div>
  )
}