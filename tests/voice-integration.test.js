import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import VoiceInput from '../VoiceInput';

// Mock Deepgram WebSocket
const mockWebSocket = {
  send: jest.fn(),
  close: jest.fn(),
  onmessage: null,
  onopen: null,
  onclose: null,
  onerror: null,
};

global.WebSocket = jest.fn(() => mockWebSocket) as any;

// Mock factory for WebSocket
const createMockWebSocket = () => ({
  ...mockWebSocket,
  send: jest.fn(),
  close: jest.fn(),
});

describe('VoiceInput Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    global.WebSocket = jest.fn(() => createMockWebSocket()) as any;
  });

  it('renders voice input button', () => {
    render(<VoiceInput onTranscript={jest.fn()} />);
    
    const voiceButton = screen.getByRole('button', { name: /voice input/i });
    expect(voiceButton).toBeInTheDocument();
  });

  it('starts recording on button click', async () => {
    render(<VoiceInput onTranscript={jest.fn()} />);
    
    const voiceButton = screen.getByRole('button', { name: /voice input/i });
    fireEvent.click(voiceButton);
    
    await waitFor(() => {
      expect(screen.getByText('Listening...')).toBeInTheDocument();
    });
  });

  it('displays transcription in real-time', async () => {
    render(<VoiceInput onTranscript={jest.fn()} />);
    
    const voiceButton = screen.getByRole('button', { name: /voice input/i });
    fireEvent.click(voiceButton);
    
    // Simulate WebSocket message
    act(() => {
      if (mockWebSocket.onmessage) {
        mockWebSocket.onmessage({
          data: JSON.stringify({ type: 'transcript', transcript: 'Hello' })
        } as any);
      }
    });
    
    await waitFor(() => {
      expect(screen.getByText('Hello')).toBeInTheDocument();
    });
  });

  it('handles voice processing state', async () => {
    render(<VoiceInput onTranscript={jest.fn()} />);
    
    const voiceButton = screen.getByRole('button', { name: /voice input/i });
    fireEvent.click(voiceButton);
    
    // Simulate processing state
    act(() => {
      if (mockWebSocket.onmessage) {
        mockWebSocket.onmessage({
          data: JSON.stringify({ type: 'processing' })
        } as any);
      }
    });
    
    await waitFor(() => {
      expect(screen.getByText('Processing...')).toBeInTheDocument();
    });
  });
});
