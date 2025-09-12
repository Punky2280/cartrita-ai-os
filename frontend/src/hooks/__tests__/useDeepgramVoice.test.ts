import { renderHook, act } from '@testing-library/react';
import { vi } from 'vitest';
import { useDeepgramVoice } from '../useDeepgramVoice';

// Mock WebSocket
const mockWebSocket = {
  send: vi.fn(),
  close: vi.fn(),
  onmessage: null,
  onopen: null,
  onclose: null,
  onerror: null,
};

global.WebSocket = vi.fn(() => mockWebSocket) as any;

describe('useDeepgramVoice', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('initializes with correct default state', () => {
    const { result } = renderHook(() => useDeepgramVoice());
    
    expect(result.current.isRecording).toBe(false);
    expect(result.current.transcript).toBe('');
  });

  it('starts recording when startRecording is called', () => {
    const { result } = renderHook(() => useDeepgramVoice());
    
    act(() => {
      result.current.startRecording();
    });
    
    expect(result.current.isRecording).toBe(true);
    expect(mockWebSocket.send).toHaveBeenCalledWith(JSON.stringify({ type: 'start_recording' }));
  });

  it('stops recording when stopRecording is called', () => {
    const { result } = renderHook(() => useDeepgramVoice());
    
    act(() => {
      result.current.startRecording();
      result.current.stopRecording();
    });
    
    expect(result.current.isRecording).toBe(false);
    expect(mockWebSocket.send).toHaveBeenCalledWith(JSON.stringify({ type: 'stop_recording' }));
  });

  it('handles transcript messages from WebSocket', () => {
    const { result } = renderHook(() => useDeepgramVoice());
    
    act(() => {
      if (mockWebSocket.onmessage) {
        mockWebSocket.onmessage({
          data: JSON.stringify({ type: 'transcript', transcript: 'Hello world' })
        } as any);
      }
    });
    
    expect(result.current.transcript).toBe('Hello world');
  });
});
