// Cartrita AI OS - Voice Output Service
// Extended TTS service with queue management and voice selection

import DeepgramVoiceService from '@/services/deepgram'
import type { VoiceSettings } from '@/types'

export interface VoiceQueueItem {
  id: string
  text: string
  voiceSettings: VoiceSettings
  priority: 'low' | 'normal' | 'high'
  timestamp: number
}

export interface VoiceOutputOptions {
  voice?: string
  speed?: number
  volume?: number
  priority?: 'low' | 'normal' | 'high'
}

export class VoiceOutputService {
  private voiceService: DeepgramVoiceService
  private queue: VoiceQueueItem[] = []
  private isProcessing = false
  private currentItem: VoiceQueueItem | null = null

  constructor(voiceService: DeepgramVoiceService) {
    this.voiceService = voiceService
  }

  // Add text to voice queue
  async enqueueSpeech(
    text: string,
    options: VoiceOutputOptions = {}
  ): Promise<string> {
    const id = `voice_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

    const queueItem: VoiceQueueItem = {
      id,
      text,
      voiceSettings: {
        enabled: true,
        language: 'en',
        voice: options.voice || 'aura-asteria-en',
        speed: options.speed || 1.0,
        volume: options.volume || 80
      },
      priority: options.priority || 'normal',
      timestamp: Date.now()
    }

    // Insert based on priority
    this.insertByPriority(queueItem)

    // Start processing if not already running
    if (!this.isProcessing) {
      this.processQueue()
    }

    return id
  }

  // Insert item into queue based on priority
  private insertByPriority(item: VoiceQueueItem): void {
    const priorityOrder = { high: 0, normal: 1, low: 2 }

    let insertIndex = this.queue.length
    for (let i = 0; i < this.queue.length; i++) {
      if (priorityOrder[item.priority] < priorityOrder[this.queue[i].priority]) {
        insertIndex = i
        break
      }
    }

    this.queue.splice(insertIndex, 0, item)
  }

  // Process the voice queue
  private async processQueue(): Promise<void> {
    if (this.isProcessing || this.queue.length === 0) {
      return
    }

    this.isProcessing = true

    try {
      while (this.queue.length > 0) {
        const item = this.queue.shift()!
        this.currentItem = item

        try {
          await this.voiceService.synthesizeSpeech(item.text, {
            model: item.voiceSettings.voice,
            voice: item.voiceSettings.voice
          })
        } catch (error) {
          console.error(`Failed to process voice item ${item.id}:`, error)
          // Continue with next item
        }

        this.currentItem = null
      }
    } finally {
      this.isProcessing = false
    }
  }

  // Speak immediately (bypass queue)
  async speakImmediately(
    text: string,
    options: VoiceOutputOptions = {}
  ): Promise<void> {
    const voiceSettings: VoiceSettings = {
      enabled: true,
      language: 'en',
      voice: options.voice || 'aura-asteria-en',
      speed: options.speed || 1.0,
      volume: options.volume || 80
    }

    await this.voiceService.synthesizeSpeech(text, {
      model: voiceSettings.voice,
      voice: voiceSettings.voice
    })
  }

  // Stop current speech and clear queue
  stop(): void {
    // Note: Deepgram doesn't provide a direct stop method
    // This would need to be implemented at the Web Audio API level
    this.queue = []
    this.currentItem = null
  }

  // Get queue status
  getQueueStatus() {
    return {
      queueLength: this.queue.length,
      isProcessing: this.isProcessing,
      currentItem: this.currentItem
    }
  }

  // Remove item from queue
  removeFromQueue(id: string): boolean {
    const index = this.queue.findIndex(item => item.id === id)
    if (index !== -1) {
      this.queue.splice(index, 1)
      return true
    }
    return false
  }

  // Clear queue
  clearQueue(): void {
    this.queue = []
  }

  // Get available voices
  getAvailableVoices() {
    return [
      { id: 'aura-asteria-en', name: 'Asteria', gender: 'female', accent: 'American' },
      { id: 'aura-luna-en', name: 'Luna', gender: 'female', accent: 'American' },
      { id: 'aura-stella-en', name: 'Stella', gender: 'female', accent: 'American' },
      { id: 'aura-athena-en', name: 'Athena', gender: 'female', accent: 'American' },
      { id: 'aura-hera-en', name: 'Hera', gender: 'female', accent: 'American' },
      { id: 'aura-orion-en', name: 'Orion', gender: 'male', accent: 'American' },
      { id: 'aura-arcas-en', name: 'Arcas', gender: 'male', accent: 'American' },
      { id: 'aura-perseus-en', name: 'Perseus', gender: 'male', accent: 'American' },
      { id: 'aura-angus-en', name: 'Angus', gender: 'male', accent: 'British' },
      { id: 'aura-orpheus-en', name: 'Orpheus', gender: 'male', accent: 'American' }
    ]
  }
}

export default VoiceOutputService
