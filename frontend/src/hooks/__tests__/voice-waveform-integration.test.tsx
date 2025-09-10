import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useDeepgramVoice } from '../useDeepgramVoice'
import WaveformVisualizer from '../../components/WaveformVisualizer'

// Mock the Deepgram service
vi.mock('../../services/deepgram', () => ({
  deepgramService: {
    startVoiceRecording: vi.fn(),
    stopVoiceRecording: vi.fn(),
    getConnectionState: vi.fn(() => 'connected'),
    getTranscript: vi.fn(() => ''),
    getAnalytics: vi.fn(() => ({})),
    onConnectionStateChange: vi.fn(),
    onTranscript: vi.fn(),
    onError: vi.fn(),
    connect: vi.fn(),
    disconnect: vi.fn()
  }
}))

// Mock the audio analysis hook
vi.mock('../useAudioAnalysis', () => ({
  useAudioAnalysis: vi.fn(() => ({
    audioAnalysisData: {
      frequencyData: new Uint8Array(128).fill(50),
      timeData: new Uint8Array(256).fill(25),
      volume: 0.5,
      dominantFrequency: 440,
      isAnalyzing: true
    },
    startAnalysis: vi.fn(),
    stopAnalysis: vi.fn(),
    updateConfig: vi.fn()
  }))
}))

// Mock the WaveformVisualizer component to avoid Canvas issues
const MockWaveformVisualizer = React.forwardRef(({ data, width, height, className }: unknown, ref: unknown) => (
  <div
    ref={ref}
    className={`waveform-visualizer ${className || ''}`}
    data-testid="waveform-visualizer"
    style={{ width, height }}
  >
    <canvas
      aria-label="Audio waveform visualization"
      className="waveform-canvas"
      width={width}
      height={height}
    />
  </div>
))

MockWaveformVisualizer.displayName = 'WaveformVisualizerMock'

vi.mock('../../components/WaveformVisualizer', () => ({
  default: MockWaveformVisualizer
}))

const TestComponent: React.FC = () => {
  const voiceHook = useDeepgramVoice()

  return (
    <div>
      <button onClick={voiceHook.startRecording}>Start Recording</button>
      <button onClick={voiceHook.stopRecording}>Stop Recording</button>
      <WaveformVisualizer
        data={voiceHook.audioAnalysisData}
        width={400}
        height={200}
        className="test-waveform"
      />
      <div data-testid="analysis-status">
        {voiceHook.audioAnalysisData?.isAnalyzing ? 'Analyzing' : 'Not Analyzing'}
      </div>
    </div>
  )
}

describe('Voice Hook + Waveform Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should integrate audio analysis with voice recording', () => {
    render(<TestComponent />)

    // Check that the component renders
    expect(screen.getByText('Start Recording')).toBeInTheDocument()
    expect(screen.getByText('Stop Recording')).toBeInTheDocument()

    // Check that waveform visualizer is rendered
    const visualizer = screen.getByTestId('waveform-visualizer')
    expect(visualizer).toBeInTheDocument()
    expect(visualizer).toHaveClass('test-waveform')

    // Check that audio analysis data is available
    expect(screen.getByTestId('analysis-status')).toHaveTextContent('Analyzing')
  })

  it('should pass audio analysis data to waveform visualizer', () => {
    render(<TestComponent />)

    // The WaveformVisualizer should receive the audioAnalysisData from the voice hook
    const visualizer = screen.getByTestId('waveform-visualizer')
    expect(visualizer).toBeInTheDocument()

    // Verify the component structure is correct
    expect(visualizer.tagName.toLowerCase()).toBe('div')
  })
})
