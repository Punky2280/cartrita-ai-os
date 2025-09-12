// Cartrita AI OS - Audio Analytics Sidebar
// Real-time conversation analytics and voice intelligence dashboard


import { useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  BarChart3,
  TrendingUp,
  Mic,
  MicOff,
  Activity,
  Brain,
  Zap,
  Volume2,
  Smile,
  Frown,
  Meh,
  ChevronLeft,
  ChevronRight
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui'
import type { Message } from '@/types'
import { useVoice } from '@/hooks/useVoice'
import { useAudioAnalysis } from '@/hooks/useAudioAnalysis'

interface AudioAnalyticsSidebarProps {
  isOpen: boolean
  onToggle: () => void
  messages: Message[]
  isStreaming: boolean
}

export default function AudioAnalyticsSidebar({
  isOpen,
  onToggle,
  messages,
  isStreaming
}: AudioAnalyticsSidebarProps) {
  const voice = useVoice()
  useAudioAnalysis()

  // Real-time conversation analytics
  const conversationAnalytics = useMemo(() => {
    const userMessages = messages.filter(m => m.role === 'user')
    const assistantMessages = messages.filter(m => m.role === 'assistant')

    const avgUserLength = userMessages.length > 0
      ? userMessages.reduce((acc, msg) => acc + (msg.content?.length || 0), 0) / userMessages.length
      : 0

    const avgAssistantLength = assistantMessages.length > 0
      ? assistantMessages.reduce((acc, msg) => acc + (msg.content?.length || 0), 0) / assistantMessages.length
      : 0

    // Use createdAt or legacy timestamp; guard against missing/invalid values
    const firstTimestamp = messages[0]?.timestamp ?? messages[0]?.createdAt
    const startMs = firstTimestamp ? Date.parse(firstTimestamp) : undefined
    const elapsedMinutes = startMs && !Number.isNaN(startMs) ? (Date.now() - startMs) / 60000 : 0
    const conversationPace = elapsedMinutes > 0 ? messages.length / elapsedMinutes : 0

    return {
      totalMessages: messages.length,
      userMessages: userMessages.length,
      assistantMessages: assistantMessages.length,
      avgUserLength: Math.round(avgUserLength),
      avgAssistantLength: Math.round(avgAssistantLength),
      conversationPace: Math.round(conversationPace * 10) / 10,
      engagement: userMessages.length > 0 ? (assistantMessages.length / userMessages.length) * 100 : 0
    }
  }, [messages])

  // Voice activity detection
  const voiceActivity = useMemo(() => {
    if (!voice.isRecording) return null

    return {
      isActive: voice.isRecording,
      signalQuality: voice.signalQuality,
      audioLevel: voice.audioLevel,
      duration: voice.getRecordingDuration(),
      confidence: voice.analytics?.sentiment?.confidence || 0
    }
  }, [voice])

  // Emotion recognition display
  const emotionDisplay = useMemo(() => {
    if (!voice.analytics?.sentiment) return null

    const { label, score } = voice.analytics.sentiment
    const confidence = Math.round(score * 100)

    const getEmotionIcon = (emotion: string) => {
      switch (emotion.toLowerCase()) {
        case 'positive':
        case 'happy':
          return <Smile className="h-4 w-4 text-green-400" />
        case 'negative':
        case 'sad':
        case 'angry':
          return <Frown className="h-4 w-4 text-red-400" />
        default:
          return <Meh className="h-4 w-4 text-yellow-400" />
      }
    }

    return {
      emotion: label,
      confidence,
      icon: getEmotionIcon(label)
    }
  }, [voice.analytics?.sentiment])

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ width: 0, opacity: 0 }}
          animate={{ width: 320, opacity: 1 }}
          exit={{ width: 0, opacity: 0 }}
          transition={{ duration: 0.3, ease: 'easeInOut' }}
          className="relative h-full bg-chatgpt-grey-dark border-l border-gray-600 overflow-hidden z-40"
        >
          {/* Toggle Button */}
          <button
            onClick={onToggle}
            className="absolute -left-3 top-1/2 transform -translate-y-1/2 z-50 h-6 w-6 bg-cartrita-blue hover:bg-cartrita-blue-light rounded-full flex items-center justify-center text-white shadow-lg"
          >
            {isOpen ? <ChevronRight className="h-3 w-3" /> : <ChevronLeft className="h-3 w-3" />}
          </button>

          {/* Content */}
          <div className="h-full flex flex-col">
            {/* Header */}
            <div className="p-4 border-b border-gray-600">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-cartrita-blue" />
                  Audio Intelligence
                </h2>
                <div className="flex items-center gap-2">
                  {voice.isRecording ? (
                    <div className="flex items-center gap-1 text-red-400">
                      <Activity className="h-4 w-4 animate-pulse" />
                      <span className="text-xs">Recording</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-1 text-gray-400">
                      <MicOff className="h-4 w-4" />
                      <span className="text-xs">Idle</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {/* Real-time Voice Activity */}
              {voiceActivity && (
                <Card className="bg-chatgpt-grey border-gray-600">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm text-white flex items-center gap-2">
                      <Mic className="h-4 w-4 text-cartrita-blue" />
                      Voice Activity
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-300">Signal Quality</span>
                      <span className="text-xs text-white">{voiceActivity.signalQuality}</span>
                    </div>
                    <div className="space-y-1">
                      <div className="flex justify-between text-xs text-gray-300">
                        <span>Audio Level</span>
                        <span>{voiceActivity.audioLevel}/255</span>
                      </div>
                      <div className="w-full bg-gray-700 rounded-full h-2">
                        <div
                          className="bg-cartrita-blue rounded-full h-2 transition-all duration-150"
                          style={{ width: `${(voiceActivity.audioLevel / 255) * 100}%` }}
                        />
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-300">Duration</span>
                      <span className="text-xs text-white">{voiceActivity.duration}s</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-300">Confidence</span>
                      <span className="text-xs text-white">{Math.round(voiceActivity.confidence * 100)}%</span>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Emotion Recognition */}
              {emotionDisplay && (
                <Card className="bg-chatgpt-grey border-gray-600">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm text-white flex items-center gap-2">
                      <Brain className="h-4 w-4 text-cartrita-blue" />
                      Emotion Analysis
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {emotionDisplay.icon}
                        <span className="text-sm text-white capitalize">{emotionDisplay.emotion}</span>
                      </div>
                      <span className="text-xs text-gray-300">{emotionDisplay.confidence}%</span>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Conversation Analytics */}
              <Card className="bg-chatgpt-grey border-gray-600">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm text-white flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-cartrita-blue" />
                    Conversation Analytics
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center">
                      <div className="text-lg font-semibold text-white">{conversationAnalytics.totalMessages}</div>
                      <div className="text-xs text-gray-300">Total Messages</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-semibold text-white">{conversationAnalytics.conversationPace}</div>
                      <div className="text-xs text-gray-300">Msgs/Min</div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between text-xs">
                      <span className="text-gray-300">User Avg Length</span>
                      <span className="text-white">{conversationAnalytics.avgUserLength} chars</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-gray-300">Assistant Avg Length</span>
                      <span className="text-white">{conversationAnalytics.avgAssistantLength} chars</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-gray-300">Engagement</span>
                      <span className="text-white">{Math.round(conversationAnalytics.engagement)}%</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Audio Intelligence Metrics */}
              <Card className="bg-chatgpt-grey border-gray-600">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm text-white flex items-center gap-2">
                    <Zap className="h-4 w-4 text-cartrita-blue" />
                    Audio Intelligence
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {voice.analytics?.language_detected && (
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-300">Detected Language</span>
                      <span className="text-xs text-white uppercase">{voice.analytics.language_detected}</span>
                    </div>
                  )}

                  {voice.analytics?.sentiment?.confidence && (
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-300">Transcription Confidence</span>
                      <span className="text-xs text-white">{Math.round(voice.analytics.sentiment.confidence * 100)}%</span>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Live Audio Visualization */}
              {voice.isRecording && (
                <Card className="bg-chatgpt-grey border-gray-600">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm text-white flex items-center gap-2">
                      <Activity className="h-4 w-4 text-cartrita-blue" />
                      Live Audio Waveform
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-16 bg-black rounded border border-gray-600 flex items-center justify-center">
                      <div className="text-xs text-gray-400 text-center">
                        <Volume2 className="h-6 w-6 mx-auto mb-1 animate-pulse" />
                        Audio waveform visualization would appear here
                        <br />
                        <span className="text-cartrita-blue">Real-time analysis active</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Streaming Status */}
              {isStreaming && (
                <Card className="bg-chatgpt-grey border-cartrita-blue/50">
                  <CardContent className="pt-4">
                    <div className="flex items-center gap-2 text-cartrita-blue">
                      <div className="animate-spin h-4 w-4 border-2 border-cartrita-blue border-t-transparent rounded-full" />
                      <span className="text-sm">AI is processing audio...</span>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
