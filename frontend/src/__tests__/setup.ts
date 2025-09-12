// Cartrita AI OS - Test Setup
// Global test configuration and utilities

import { expect, afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'

// Extend expect with jest-dom matchers
expect.extend(matchers)

// Cleanup after each test
afterEach(() => {
  cleanup()
})

// Mock environment variables
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock WebSocket
const MockWebSocket = vi.fn().mockImplementation(() => ({
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  dispatchEvent: vi.fn(),
  send: vi.fn(),
  close: vi.fn(),
  readyState: 1
}))

MockWebSocket.CONNECTING = 0
MockWebSocket.OPEN = 1
MockWebSocket.CLOSING = 2
MockWebSocket.CLOSED = 3

global.WebSocket = MockWebSocket

// Mock MediaDevices
Object.defineProperty(navigator, 'mediaDevices', {
  value: {
    getUserMedia: vi.fn().mockResolvedValue({
      getTracks: () => [{ stop: vi.fn() }],
      getAudioTracks: () => [{ stop: vi.fn() }],
      getVideoTracks: () => []
    })
  },
  writable: true
})

// Mock AudioContext
global.AudioContext = vi.fn().mockImplementation(() => ({
  createMediaStreamSource: vi.fn(),
  createAnalyser: vi.fn(),
  createGain: vi.fn(),
  decodeAudioData: vi.fn().mockResolvedValue({}),
  suspend: vi.fn(),
  resume: vi.fn()
}))

// Mock MediaRecorder
const MockMediaRecorder = vi.fn().mockImplementation(() => ({
  start: vi.fn(),
  stop: vi.fn(),
  pause: vi.fn(),
  resume: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  dispatchEvent: vi.fn(),
  state: 'inactive',
  mimeType: 'audio/webm',
  ondataavailable: null,
  onstop: null,
  onerror: null
}))

MockMediaRecorder.isTypeSupported = vi.fn().mockReturnValue(true)

global.MediaRecorder = MockMediaRecorder

// Global test utilities
global.testUtils = {
  createMockTranscription: (text: string, isFinal = false) => ({
    text,
    confidence: 0.95,
    is_final: isFinal,
    speaker: 1,
    timestamp: Date.now(),
    words: text.split(' ').map((word, index) => ({
      word,
      start: index * 0.5,
      end: (index + 1) * 0.5,
      confidence: 0.95
    }))
  }),

  createMockAnalytics: () => ({
    sentiment: {
      score: 0.8,
      label: 'positive' as const,
      confidence: 0.9
    },
    topics: [{
      name: 'technology',
      confidence: 0.85,
      keywords: ['ai', 'machine learning']
    }],
    emotions: [{
      emotion: 'joy',
      confidence: 0.7
    }],
    speaker_id: 'speaker_1',
    language_detected: 'en-US'
  }),

  waitForNextTick: () => new Promise(resolve => setTimeout(resolve, 0))
}
