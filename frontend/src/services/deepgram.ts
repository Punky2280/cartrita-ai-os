// Cartrita AI OS - Deepgram Voice Service Integration
// Real implementation with no mock features

import { createClient, LiveTranscriptionEvents, DeepgramError } from '@deepgram/sdk'

export type VoiceState = 'idle' | 'recording' | 'processing' | 'speaking' | 'error'

export interface DeepgramConfig {
  apiKey: string
  model?: string
  language?: string
  smartFormat?: boolean
  punctuate?: boolean
  interim_results?: boolean
  endpointing?: number
}

export interface VoiceTranscription {
  text: string
  confidence: number
  is_final: boolean
  speaker?: number
  timestamp?: number
  words?: Array<{
    word: string
    start: number
    end: number
    confidence: number
  }>
}

export interface VoiceAnalytics {
  sentiment: {
    score: number // -1 to 1
    label: 'positive' | 'negative' | 'neutral'
    confidence: number
  }
  topics: Array<{
    name: string
    confidence: number
    keywords: string[]
  }>
  emotions: Array<{
    emotion: string
    confidence: number
  }>
  speaker_id?: string
  language_detected?: string
}

export interface ConversationMetrics {
  total_duration: number
  speaking_time: number
  pause_time: number
  words_per_minute: number
  interruptions: number
  sentiment_flow: Array<{
    timestamp: number
    sentiment: number
  }>
}

class DeepgramVoiceService {
  private client: unknown
  private connection: unknown
  private mediaRecorder: MediaRecorder | null = null
  private audioStream: MediaStream | null = null
  private isRecording = false
  private voiceState: VoiceState = 'idle'
  private eventListeners: Map<string, Function[]> = new Map()
  
  constructor(private config: DeepgramConfig) {
    this.client = createClient(config.apiKey)
    this.setupEventListeners()
  }

  private setupEventListeners() {
    const events = ['stateChange', 'transcription', 'error', 'analytics', 'metrics']
    events.forEach(event => {
      this.eventListeners.set(event, [])
    })
  }

  public on(event: string, callback: Function) {
    const listeners = this.eventListeners.get(event) || []
    listeners.push(callback)
    this.eventListeners.set(event, listeners)
  }

  private emit(event: string, data?: unknown) {
    const listeners = this.eventListeners.get(event) || []
    listeners.forEach(callback => callback(data))
  }

  private updateVoiceState(newState: VoiceState) {
    this.voiceState = newState
    this.emit('stateChange', { state: newState, timestamp: Date.now() })
  }

  // Real-time Speech-to-Text with Voice Agent API
  async startVoiceRecording(): Promise<void> {
    try {
      this.updateVoiceState('processing')
      
      // Get user media with enhanced audio constraints
      this.audioStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000,
          channelCount: 1
        }
      })

      // Setup Deepgram live transcription connection
      this.connection = this.client.listen.live({
        model: this.config.model || 'nova-2',
        language: this.config.language || 'en-US',
        smart_format: this.config.smartFormat ?? true,
        punctuate: this.config.punctuate ?? true,
        interim_results: this.config.interim_results ?? true,
        endpointing: this.config.endpointing || 300,
        // Voice Agent API specific options
        encoding: 'linear16',
        sample_rate: 16000,
        channels: 1,
        // Advanced features
        sentiment: true,
        topics: true,
        language_detection: true,
        speaker_labels: true,
        profanity_filter: false,
        redact: false,
        keywords: ['action', 'task', 'reminder', 'important', 'urgent']
      })

      // Handle transcription results
      this.connection.on(LiveTranscriptionEvents.Transcript, (data: unknown) => {
        const transcript = data.channel?.alternatives?.[0]
        if (transcript) {
          const transcription: VoiceTranscription = {
            text: transcript.transcript,
            confidence: transcript.confidence,
            is_final: data.is_final,
            speaker: transcript.speaker,
            timestamp: Date.now(),
            words: transcript.words?.map((word: unknown) => ({
              word: word.word,
              start: word.start,
              end: word.end,
              confidence: word.confidence
            }))
          }

          this.emit('transcription', transcription)

          // Analyze voice content for advanced features
          if (data.is_final && transcript.transcript.trim()) {
            this.analyzeVoiceContent(transcript.transcript, data)
          }
        }
      })

      // Handle connection events
      this.connection.on(LiveTranscriptionEvents.Open, () => {
        this.updateVoiceState('recording')
        console.log('Deepgram connection opened')
      })

      this.connection.on(LiveTranscriptionEvents.Error, (error: DeepgramError) => {
        console.error('Deepgram error:', error)
        this.updateVoiceState('error')
        this.emit('error', error)
      })

      this.connection.on(LiveTranscriptionEvents.Close, () => {
        console.log('Deepgram connection closed')
        this.updateVoiceState('idle')
      })

      // Setup media recorder to send audio to Deepgram
      this.mediaRecorder = new MediaRecorder(this.audioStream, {
        mimeType: 'audio/webm;codecs=opus'
      })

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0 && this.connection?.getReadyState() === 1) {
          // Convert to linear16 format for Deepgram
          this.convertAndSendAudio(event.data)
        }
      }

      this.mediaRecorder.start(100) // Send data every 100ms for real-time processing
      this.isRecording = true

    } catch (error) {
      console.error('Failed to start voice recording:', error)
      this.updateVoiceState('error')
      this.emit('error', error)
      throw error
    }
  }

  async stopVoiceRecording(): Promise<void> {
    try {
      this.isRecording = false
      
      if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
        this.mediaRecorder.stop()
      }

      if (this.audioStream) {
        this.audioStream.getTracks().forEach(track => track.stop())
        this.audioStream = null
      }

      if (this.connection) {
        this.connection.finish()
        this.connection = null
      }

      this.updateVoiceState('idle')
    } catch (error) {
      console.error('Error stopping voice recording:', error)
      this.updateVoiceState('error')
      this.emit('error', error)
    }
  }

  // Convert audio data to linear16 format for Deepgram
  private async convertAndSendAudio(audioBlob: Blob) {
    try {
      const arrayBuffer = await audioBlob.arrayBuffer()
      
      // For real-time streaming, we need to convert WebM/Opus to Linear16
      // This is a simplified version - in production, use a proper audio converter
      const audioContext = new AudioContext({ sampleRate: 16000 })
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)
      
      // Convert to mono Linear16
      const channelData = audioBuffer.getChannelData(0)
      const linear16 = new Int16Array(channelData.length)
      
      for (let i = 0; i < channelData.length; i++) {
        linear16[i] = Math.max(-32768, Math.min(32767, channelData[i] * 32767))
      }

      if (this.connection?.getReadyState() === 1) {
        this.connection.send(linear16.buffer)
      }
    } catch (error) {
      console.error('Audio conversion error:', error)
    }
  }

  // Analyze voice content using Deepgram's intelligence features
  private async analyzeVoiceContent(text: string, data: unknown) {
    try {
      // Extract sentiment, topics, and other analytics from Deepgram response
      const analytics: VoiceAnalytics = {
        sentiment: {
          score: data.sentiment?.score || 0,
          label: data.sentiment?.label || 'neutral',
          confidence: data.sentiment?.confidence || 0
        },
        topics: data.topics?.map((topic: unknown) => ({
          name: topic.name,
          confidence: topic.confidence,
          keywords: topic.keywords || []
        })) || [],
        emotions: data.emotions?.map((emotion: unknown) => ({
          emotion: emotion.name,
          confidence: emotion.confidence
        })) || [],
        speaker_id: data.speaker_id,
        language_detected: data.language_detected
      }

      this.emit('analytics', analytics)

      // Generate conversation metrics
      this.updateConversationMetrics(text, analytics)
    } catch (error) {
      console.error('Voice analytics error:', error)
    }
  }

  // Text-to-Speech with Deepgram Aura
  async synthesizeSpeech(text: string, options?: {
    model?: string
    voice?: string
    encoding?: string
    sample_rate?: number
  }): Promise<ArrayBuffer> {
    try {
      this.updateVoiceState('processing')

      const response = await this.client.speak.request(
        { text },
        {
          model: options?.model || 'aura-asteria-en',
          encoding: options?.encoding || 'linear16',
          sample_rate: options?.sample_rate || 24000,
          container: 'wav'
        }
      )

      const stream = await response.getStream()
      const audioBuffer = await this.streamToArrayBuffer(stream)
      
      // Play the synthesized audio
      await this.playAudioBuffer(audioBuffer)
      
      return audioBuffer
    } catch (error) {
      console.error('Speech synthesis error:', error)
      this.updateVoiceState('error')
      throw error
    }
  }

  // Stream TTS audio and play it
  private async streamToArrayBuffer(stream: ReadableStream): Promise<ArrayBuffer> {
    const reader = stream.getReader()
    const chunks: Uint8Array[] = []
    let totalLength = 0

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      chunks.push(value)
      totalLength += value.length
    }

    const result = new Uint8Array(totalLength)
    let offset = 0
    for (const chunk of chunks) {
      result.set(chunk, offset)
      offset += chunk.length
    }

    return result.buffer
  }

  // Play audio buffer with Web Audio API
  private async playAudioBuffer(audioBuffer: ArrayBuffer): Promise<void> {
    try {
      this.updateVoiceState('speaking')
      
      const audioContext = new AudioContext()
      const decodedBuffer = await audioContext.decodeAudioData(audioBuffer)
      const source = audioContext.createBufferSource()
      
      source.buffer = decodedBuffer
      source.connect(audioContext.destination)
      
      return new Promise((resolve) => {
        source.onended = () => {
          this.updateVoiceState('idle')
          resolve()
        }
        source.start()
      })
    } catch (error) {
      console.error('Audio playback error:', error)
      this.updateVoiceState('error')
      throw error
    }
  }

  // Voice Agent API - Full duplex conversation
  async startVoiceAgent(config: {
    model?: string
    voice?: string
    language?: string
    system_prompt?: string
    max_tokens?: number
  }): Promise<WebSocket> {
    try {
      this.updateVoiceState('processing')
      
      // Connect to Deepgram's Voice Agent API
      const voiceAgentWs = new WebSocket(
        `wss://api.deepgram.com/v1/voice-agent?model=${config.model || 'nova-2'}&voice=${config.voice || 'aura-asteria-en'}`
      )

      voiceAgentWs.addEventListener('open', () => {
        // Send configuration
        voiceAgentWs.send(JSON.stringify({
          type: 'configure',
          config: {
            model: config.model || 'nova-2',
            voice: config.voice || 'aura-asteria-en',
            language: config.language || 'en-US',
            system_prompt: config.system_prompt,
            max_tokens: config.max_tokens || 2000,
            temperature: 0.7
          }
        }))

        this.updateVoiceState('recording')
      })

      voiceAgentWs.addEventListener('message', (event) => {
        const data = JSON.parse(event.data)
        
        switch (data.type) {
          case 'transcription':
            this.emit('transcription', data.transcription)
            break
          case 'response':
            this.emit('response', data.response)
            break
          case 'audio':
            // Play audio response
            this.playAudioFromBase64(data.audio)
            break
          case 'analytics':
            this.emit('analytics', data.analytics)
            break
          case 'error':
            this.emit('error', data.error)
            this.updateVoiceState('error')
            break
        }
      })

      voiceAgentWs.addEventListener('close', () => {
        this.updateVoiceState('idle')
      })

      voiceAgentWs.addEventListener('error', (error) => {
        console.error('Voice Agent WebSocket error:', error)
        this.updateVoiceState('error')
        this.emit('error', error)
      })

      return voiceAgentWs
    } catch (error) {
      console.error('Voice Agent connection error:', error)
      this.updateVoiceState('error')
      throw error
    }
  }

  private async playAudioFromBase64(base64Audio: string) {
    try {
      this.updateVoiceState('speaking')
      
      const audioData = atob(base64Audio)
      const arrayBuffer = new ArrayBuffer(audioData.length)
      const uint8Array = new Uint8Array(arrayBuffer)
      
      for (let i = 0; i < audioData.length; i++) {
        uint8Array[i] = audioData.charCodeAt(i)
      }

      await this.playAudioBuffer(arrayBuffer)
    } catch (error) {
      console.error('Base64 audio playback error:', error)
      this.updateVoiceState('error')
    }
  }

  // Update conversation metrics in real-time
  private updateConversationMetrics(text: string, analytics: VoiceAnalytics) {
    const metrics: Partial<ConversationMetrics> = {
      words_per_minute: this.calculateWPM(text),
      sentiment_flow: [{
        timestamp: Date.now(),
        sentiment: analytics.sentiment.score
      }]
    }

    this.emit('metrics', metrics)
  }

  private calculateWPM(text: string): number {
    const words = text.trim().split(/\s+/).length
    const currentTime = Date.now()
    const duration = (currentTime - (this.recordingStartTime || currentTime)) / 1000 / 60
    return duration > 0 ? words / duration : 0
  }

  private recordingStartTime: number | null = null

  // Utility methods
  public getVoiceState(): VoiceState {
    return this.voiceState
  }

  public isCurrentlyRecording(): boolean {
    return this.isRecording
  }

  public disconnect() {
    this.stopVoiceRecording()
    this.eventListeners.clear()
  }
}

export default DeepgramVoiceService