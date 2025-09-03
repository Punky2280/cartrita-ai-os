// Cartrita AI OS - Voice Input Component
// Advanced voice input with real-time transcription and visual feedback

'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import {
  Mic,
  MicOff,
  Square,
  RotateCcw,
  Volume2,
  VolumeX,
  Settings,
  CheckCircle,
  AlertCircle,
  Loader2
} from 'lucide-react'
import { cn } from '@/utils'
import {
  Button,
  Badge,
  Slider,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Alert,
  AlertDescription
} from '@/components/ui'
import { useTranscribeAudio } from '@/hooks'
import type { VoiceSettings } from '@/types'

// Voice visualization component
function VoiceVisualizer({
  isRecording,
  volume = 0,
  className
}: {
  isRecording: boolean
  volume?: number
  className?: string
}) {
  const bars = 20
  const getBarHeight = (index: number) => {
    if (!isRecording) return 4
    const baseHeight = 4
    const maxHeight = 32
    const variation = Math.sin((Date.now() * 0.01) + (index * 0.5)) * 0.5 + 0.5
    const volumeMultiplier = volume / 100
    return baseHeight + (maxHeight - baseHeight) * variation * volumeMultiplier
  }

  return (
    <div className={cn('flex items-end justify-center gap-1', className)}>
      {Array.from({ length: bars }).map((_, i) => (
        <motion.div
          key={i}
          className="w-1 bg-primary rounded-full"
          animate={{
            height: getBarHeight(i),
            opacity: isRecording ? [0.3, 1, 0.3] : 0.3
          }}
          transition={{
            duration: 0.1,
            repeat: isRecording ? Infinity : 0,
            ease: 'easeInOut'
          }}
        />
      ))}
    </div>
  )
}

// Recording timer component
function RecordingTimer({
  startTime,
  isRecording
}: {
  startTime: number | null
  isRecording: boolean
}) {
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    if (!isRecording || !startTime) {
      setElapsed(0)
      return
    }

    const interval = setInterval(() => {
      setElapsed(Date.now() - startTime)
    }, 100)

    return () => clearInterval(interval)
  }, [isRecording, startTime])

  const formatTime = (ms: number) => {
    const seconds = Math.floor(ms / 1000)
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
  }

  return (
    <motion.div
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className="text-lg font-mono font-medium text-primary"
    >
      {formatTime(elapsed)}
    </motion.div>
  )
}

// Main Voice Input Component
interface VoiceInputProps {
  onTranscript: (transcript: string) => void
  onCancel: () => void
  voiceSettings?: VoiceSettings
  className?: string
  maxDuration?: number // in seconds
  autoStart?: boolean
}

export function VoiceInput({
  onTranscript,
  onCancel,
  voiceSettings,
  className,
  maxDuration = 300, // 5 minutes
  autoStart = false
}: VoiceInputProps) {
  const [isRecording, setIsRecording] = useState(autoStart)
  const [volume, setVolume] = useState(0)
  const [transcript, setTranscript] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [startTime, setStartTime] = useState<number | null>(null)
  const [showSettings, setShowSettings] = useState(false)

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const animationFrameRef = useRef<number>()

  const transcribeAudio = useTranscribeAudio()

  // Initialize audio context and analyser for volume visualization
  const initializeAudioAnalysis = useCallback(async (stream: MediaStream) => {
    try {
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)()
      analyserRef.current = audioContextRef.current.createAnalyser()
      const source = audioContextRef.current.createMediaStreamSource(stream)
      source.connect(analyserRef.current)
      analyserRef.current.fftSize = 256

      const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount)

      const updateVolume = () => {
        if (analyserRef.current && isRecording) {
          analyserRef.current.getByteFrequencyData(dataArray)
          const average = dataArray.reduce((a, b) => a + b) / dataArray.length
          setVolume(Math.round((average / 255) * 100))
          animationFrameRef.current = requestAnimationFrame(updateVolume)
        }
      }

      updateVolume()
    } catch (error) {
      console.warn('Audio analysis not available:', error)
    }
  }, [isRecording])

  // Start recording
  const startRecording = useCallback(async () => {
    try {
      setError(null)
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 44100
        }
      })

      streamRef.current = stream
      await initializeAudioAnalysis(stream)

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })

      mediaRecorderRef.current = mediaRecorder
      chunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' })

        // Stop all tracks
        stream.getTracks().forEach(track => track.stop())

        // Clean up
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current)
        }
        if (audioContextRef.current) {
          audioContextRef.current.close()
        }

        // Process the recording
        await processRecording(audioBlob)
      }

      mediaRecorder.start(100) // Collect data every 100ms
      setIsRecording(true)
      setStartTime(Date.now())

      toast.success('Recording started')
    } catch (error) {
      console.error('Failed to start recording:', error)
      setError('Failed to access microphone. Please check permissions.')
      toast.error('Failed to start recording')
    }
  }, [initializeAudioAnalysis])

  // Stop recording
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      setStartTime(null)
    }
  }, [isRecording])

  // Process recording
  const processRecording = useCallback(async (audioBlob: Blob) => {
    setIsProcessing(true)
    setError(null)

    try {
      const file = new File([audioBlob], 'recording.webm', { type: 'audio/webm' })

      const result = await transcribeAudio.mutateAsync(file) as any

      if (result.success && result.data) {
        const transcribedText = result.data.text
        setTranscript(transcribedText)
        onTranscript(transcribedText)
        toast.success('Transcription complete')
      } else {
        throw new Error('Transcription failed')
      }
    } catch (error) {
      console.error('Transcription error:', error)
      setError('Failed to transcribe audio. Please try again.')
      toast.error('Transcription failed')
    } finally {
      setIsProcessing(false)
    }
  }, [transcribeAudio, onTranscript])

  // Cancel recording
  const cancelRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
    }

    // Stop all tracks
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
    }

    // Clean up
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current)
    }
    if (audioContextRef.current) {
      audioContextRef.current.close()
    }

    setIsRecording(false)
    setStartTime(null)
    setVolume(0)
    onCancel()
  }, [isRecording, onCancel])

  // Auto-stop after max duration
  useEffect(() => {
    if (isRecording && startTime) {
      const timeout = setTimeout(() => {
        stopRecording()
      }, maxDuration * 1000)

      return () => clearTimeout(timeout)
    }
  }, [isRecording, startTime, maxDuration, stopRecording])

  // Auto-start if requested
  useEffect(() => {
    if (autoStart && !isRecording) {
      startRecording()
    }
  }, [autoStart, isRecording, startRecording])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (mediaRecorderRef.current && isRecording) {
        mediaRecorderRef.current.stop()
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
      if (audioContextRef.current) {
        audioContextRef.current.close()
      }
    }
  }, [isRecording])

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className={cn('w-full max-w-md', className)}
      >
        <Card>
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                {isRecording ? (
                  <Mic className="h-5 w-5 text-red-500" />
                ) : (
                  <MicOff className="h-5 w-5" />
                )}
                Voice Input
              </CardTitle>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowSettings(!showSettings)}
                  className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-accent hover:text-accent-foreground h-9 rounded-md px-3"
                >
                  <Settings className="h-4 w-4" />
                </button>
                <button
                  onClick={cancelRecording}
                  className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-accent hover:text-accent-foreground h-9 rounded-md px-3"
                >
                  <Square className="h-4 w-4" />
                </button>
              </div>
            </div>
          </CardHeader>

          <CardContent className="space-y-4">
            {/* Voice Visualizer */}
            <div className="flex flex-col items-center gap-4">
              <VoiceVisualizer
                isRecording={isRecording}
                volume={volume}
                className="h-16"
              />

              {isRecording && startTime && (
                <RecordingTimer startTime={startTime} isRecording={isRecording} />
              )}
            </div>

            {/* Controls */}
            <div className="flex items-center justify-center gap-4">
              {!isRecording ? (
                <button
                  onClick={startRecording}
                  className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2 flex items-center gap-2"
                  disabled={isProcessing}
                >
                  <Mic className="h-4 w-4" />
                  Start Recording
                </button>
              ) : (
                <button
                  onClick={stopRecording}
                  className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-destructive text-destructive-foreground hover:bg-destructive/90 h-10 px-4 py-2 flex items-center gap-2"
                >
                  <Square className="h-4 w-4" />
                  Stop Recording
                </button>
              )}

              {isRecording && (
                <button
                  onClick={cancelRecording}
                  className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-9 rounded-md px-3"
                >
                  Cancel
                </button>
              )}
            </div>

            {/* Processing State */}
            {isProcessing && (
              <div className="flex items-center justify-center gap-2 text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Processing audio...</span>
              </div>
            )}

            {/* Transcript */}
            {transcript && (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span className="text-sm font-medium">Transcript</span>
                </div>
                <div className="p-3 bg-muted rounded-lg">
                  <p className="text-sm">{transcript}</p>
                </div>
              </div>
            )}

            {/* Error */}
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Settings */}
            {showSettings && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="space-y-4 pt-4 border-t"
              >
                <div className="space-y-2">
                  <label className="text-sm font-medium">Voice Settings</label>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <label className="text-xs text-muted-foreground">Speed</label>
                      <Slider
                        value={[voiceSettings?.speed || 1]}
                        min={0.5}
                        max={2}
                        step={0.1}
                        className="w-full"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs text-muted-foreground">Pitch</label>
                      <Slider
                        value={[voiceSettings?.pitch || 1]}
                        min={0.5}
                        max={2}
                        step={0.1}
                        className="w-full"
                      />
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Tips */}
            <div className="text-xs text-muted-foreground space-y-1">
              <p>• Speak clearly and at a normal pace</p>
              <p>• Maximum recording time: {maxDuration} seconds</p>
              <p>• Make sure your microphone is enabled</p>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </AnimatePresence>
  )
}

// Compact voice input button
export function VoiceInputButton({
  onTranscript,
  isActive = false,
  className
}: {
  onTranscript: (transcript: string) => void
  isActive?: boolean
  className?: string
}) {
  const [isRecording, setIsRecording] = useState(false)

  const handleClick = () => {
    if (isRecording) {
      setIsRecording(false)
    } else {
      setIsRecording(true)
      // In a real implementation, this would open a modal or inline voice input
      toast.info('Voice input would open here')
    }
  }

  return (
    <button
      onClick={handleClick}
      className={cn(
        'relative inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 rounded-md px-3',
        isRecording ? 'bg-destructive text-destructive-foreground hover:bg-destructive/90 animate-pulse' : 'hover:bg-accent hover:text-accent-foreground',
        className
      )}
    >
      {isRecording ? (
        <MicOff className="h-4 w-4" />
      ) : (
        <Mic className="h-4 w-4" />
      )}
      {isRecording && (
        <motion.div
          className="absolute inset-0 rounded-full border-2 border-red-500"
          animate={{ scale: [1, 1.2, 1] }}
          transition={{ duration: 1, repeat: Infinity }}
        />
      )}
    </button>
  )
}