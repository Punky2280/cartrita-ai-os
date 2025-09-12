// Cartrita AI OS - Enhanced Deepgram Voice Hook
// Production-ready WebSocket integration with real-time transcription

import { useState, useEffect, useRef, useCallback } from 'react'
import DeepgramVoiceService, { VoiceState, VoiceTranscription, VoiceAnalytics, DeepgramConfig } from '../services/deepgram'
import { useAudioAnalysis, AudioAnalysisData } from './useAudioAnalysis'

export interface WebSocketMessage {
  type: 'transcript' | 'analytics' | 'error' | 'state' | 'metrics'
  data: unknown
  timestamp: number
}

export interface UseDeepgramVoiceOptions {
  config?: Partial<DeepgramConfig>
  autoReconnect?: boolean
  reconnectAttempts?: number
  reconnectDelay?: number
}

export interface UseDeepgramVoiceReturn {
  // State
  isRecording: boolean
  isConnected: boolean
  voiceState: VoiceState
  transcript: string
  interimTranscript: string
  finalTranscript: string
  analytics: VoiceAnalytics | null
  error: string | null
  audioAnalysisData: AudioAnalysisData | null

  // Actions
  startRecording: () => Promise<void>
  stopRecording: () => Promise<void>
  clearTranscript: () => void
  reconnect: () => Promise<void>

  // Connection management
  connectionState: 'connecting' | 'connected' | 'disconnected' | 'error'
  lastActivity: number | null
}

export const useDeepgramVoice = (options: UseDeepgramVoiceOptions = {}): UseDeepgramVoiceReturn => {
  const {
    config = {},
    autoReconnect = true,
    reconnectAttempts = 3,
    reconnectDelay = 1000
  } = options

  // State management
  const [isRecording, setIsRecording] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [voiceState, setVoiceState] = useState<VoiceState>('idle')
  const [transcript, setTranscript] = useState('')
  const [interimTranscript, setInterimTranscript] = useState('')
  const [finalTranscript, setFinalTranscript] = useState('')
  const [analytics, setAnalytics] = useState<VoiceAnalytics | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [connectionState, setConnectionState] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected')
  const [lastActivity, setLastActivity] = useState<number | null>(null)

  // Refs
  const serviceRef = useRef<DeepgramVoiceService | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectCountRef = useRef(0)
  const streamRef = useRef<MediaStream | null>(null)

  // Audio analysis for waveform visualization
  const { analysisData: audioAnalysisData, startAnalysis, stopAnalysis } = useAudioAnalysis({
    enabled: true,
    config: {
      fftSize: 2048,
      smoothingTimeConstant: 0.8
    }
  })

  // Default configuration
  const defaultConfig: DeepgramConfig = {
    apiKey: process.env.NEXT_PUBLIC_DEEPGRAM_API_KEY || '',
    model: 'nova-2',
    language: 'en-US',
    smartFormat: true,
    punctuate: true,
    interim_results: true,
    endpointing: 300,
    ...config
  }

  // Initialize service
  const initializeService = useCallback(async () => {
    try {
      if (!defaultConfig.apiKey) {
        throw new Error('Deepgram API key is required')
      }

      serviceRef.current = new DeepgramVoiceService(defaultConfig)

      // Set up event listeners
      serviceRef.current.on('stateChange', (data: { state: VoiceState; timestamp: number }) => {
        setVoiceState(data.state)
        setIsRecording(data.state === 'recording')
        setLastActivity(data.timestamp)
      })

      serviceRef.current.on('transcription', (transcription: VoiceTranscription) => {
        if (transcription.is_final) {
          const newFinal = transcription.text
          setFinalTranscript(prev => prev + ' ' + newFinal)
          setTranscript(prev => prev + ' ' + newFinal)
          setInterimTranscript('')
        } else {
          setInterimTranscript(transcription.text)
          setTranscript(prev => {
            // Remove previous interim and add new one
            const withoutInterim = prev.replace(interimTranscript, '').trim()
            return withoutInterim + ' ' + transcription.text
          })
        }
        setLastActivity(Date.now())
      })

      serviceRef.current.on('analytics', (analyticsData: VoiceAnalytics) => {
        setAnalytics(analyticsData)
        setLastActivity(Date.now())
      })

      serviceRef.current.on('error', (errorData: unknown) => {
        const errorMessage = (errorData as any)?.message || 'Unknown error occurred'
        setError(errorMessage)
        setConnectionState('error')
        console.error('Deepgram voice error:', errorData)
      })

      setConnectionState('connected')
      setIsConnected(true)
      setError(null)
      reconnectCountRef.current = 0

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to initialize voice service'
      setError(errorMessage)
      setConnectionState('error')
      setIsConnected(false)
    }
  }, [defaultConfig, finalTranscript])

  // Cleanup function
  const cleanup = useCallback(() => {
    if (serviceRef.current) {
      serviceRef.current = null
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
  }, [])

  // Reconnection logic
  const reconnect = useCallback(async () => {
    if (reconnectCountRef.current >= reconnectAttempts) {
      setError('Maximum reconnection attempts reached')
      return
    }

    setConnectionState('connecting')
    reconnectCountRef.current += 1

    reconnectTimeoutRef.current = setTimeout(async () => {
      try {
        await initializeService()
      } catch (err) {
        if (autoReconnect && reconnectCountRef.current < reconnectAttempts) {
          reconnect()
        }
      }
    }, reconnectDelay * reconnectCountRef.current)
  }, [initializeService, autoReconnect, reconnectAttempts, reconnectDelay])

  // Start recording
  const startRecording = useCallback(async () => {
    try {
      if (!serviceRef.current) {
        await initializeService()
      }

      if (serviceRef.current) {
        await serviceRef.current.startVoiceRecording()
        setVoiceState('recording')
        setIsRecording(true)
        setError(null)

        // Start audio analysis for waveform visualization
        // Access the stream from the service (we'll need to add a getter)
        const stream = (serviceRef.current as any).audioStream
        if (stream) {
          streamRef.current = stream
          await startAnalysis(stream)
        }
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start recording'
      setError(errorMessage)
      throw err
    }
  }, [initializeService, startAnalysis])

  // Stop recording
  const stopRecording = useCallback(async () => {
    try {
      if (serviceRef.current) {
        await serviceRef.current.stopVoiceRecording()
        setVoiceState('idle')
        setIsRecording(false)
      }

      // Stop audio analysis
      stopAnalysis()
      streamRef.current = null

      setError(null)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to stop recording'
      setError(errorMessage)
      throw err
    }
  }, [stopAnalysis])

  // Clear transcript
  const clearTranscript = useCallback(() => {
    setTranscript('')
    setInterimTranscript('')
    setFinalTranscript('')
    setAnalytics(null)
  }, [])

  // Initialize on mount
  useEffect(() => {
    // Only initialize if we have an API key
    if (defaultConfig.apiKey) {
      initializeService()
    } else {
      setError('Deepgram API key is required')
      setConnectionState('error')
    }

    return () => {
      cleanup()
    }
  }, [initializeService, cleanup, defaultConfig.apiKey])

  // Handle connection state changes
  useEffect(() => {
    if (!isConnected && autoReconnect && connectionState === 'disconnected') {
      reconnect()
    }
  }, [isConnected, autoReconnect, connectionState, reconnect])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanup()
    }
  }, [cleanup])

  return {
    // State
    isRecording,
    isConnected,
    voiceState,
    transcript,
    interimTranscript,
    finalTranscript,
    analytics,
    error,
    audioAnalysisData,

    // Actions
    startRecording,
    stopRecording,
    clearTranscript,
    reconnect,

    // Connection management
    connectionState,
    lastActivity
  }
}