// Cartrita AI OS - Enhanced Deepgram Voice Hook Tests
// Comprehensive tests for production-ready WebSocket integration

// Mock must be at the very top
const mockStartVoiceRecording = vi.fn();
const mockStopVoiceRecording = vi.fn();
const mockConnect = vi.fn();

vi.mock("@/services/deepgram", () => {
  class MockDeepgramVoiceService {
    startVoiceRecording = mockStartVoiceRecording.mockImplementation(() => {
      console.log("Mock startVoiceRecording called");
      return Promise.resolve();
    });
    stopVoiceRecording = mockStopVoiceRecording.mockImplementation(() => {
      console.log("Mock stopVoiceRecording called");
      return Promise.resolve();
    });
    connect = mockConnect.mockImplementation(() => {
      console.log("Mock connect called");
      return Promise.resolve();
    });
    on = vi.fn();
    emit = vi.fn();
  }

  return {
    __esModule: true,
    default: MockDeepgramVoiceService,
    DeepgramVoiceService: MockDeepgramVoiceService,
    VoiceState: {},
    VoiceTranscription: {},
    VoiceAnalytics: {},
    DeepgramConfig: {},
  };
});

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import React from "react";

import { useDeepgramVoice } from "@/hooks/useDeepgramVoice";

// Mock environment variables
const mockApiKey = "test-deepgram-api-key";
vi.stubEnv("NEXT_PUBLIC_DEEPGRAM_API_KEY", mockApiKey);

// Mock MediaDevices
const mockGetUserMedia = vi.fn();
Object.defineProperty(navigator, "mediaDevices", {
  value: {
    getUserMedia: mockGetUserMedia,
  },
  writable: true,
});

// Mock AudioContext
global.AudioContext = vi.fn().mockImplementation(() => ({
  createMediaStreamSource: vi.fn(),
  createAnalyser: vi.fn(),
  createGain: vi.fn(),
  decodeAudioData: vi.fn().mockResolvedValue({}),
  suspend: vi.fn(),
  resume: vi.fn(),
}));

// Mock MediaRecorder
const MockMediaRecorder = vi.fn().mockImplementation(() => ({
  start: vi.fn(),
  stop: vi.fn(),
  pause: vi.fn(),
  resume: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  dispatchEvent: vi.fn(),
  state: "inactive",
  mimeType: "audio/webm",
  ondataavailable: null,
  onstop: null,
  onerror: null,
}));

// Add static method to MediaRecorder mock
Object.defineProperty(MockMediaRecorder, "isTypeSupported", {
  value: vi.fn().mockReturnValue(true),
});
global.MediaRecorder = MockMediaRecorder as any;

describe("useDeepgramVoice", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetUserMedia.mockResolvedValue({
      getTracks: () => [{ stop: vi.fn() }],
    });
    mockConnect.mockResolvedValue(undefined);
    mockStartVoiceRecording.mockResolvedValue(undefined);
    mockStopVoiceRecording.mockResolvedValue(undefined);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("Initialization", () => {
    it("should initialize with default state", async () => {
      const { result } = renderHook(() => useDeepgramVoice());

      // Wait for initialization to complete
      await waitFor(() => {
        expect(result.current.connectionState).toBe("connected");
      });

      expect(result.current.isRecording).toBe(false);
      expect(result.current.isConnected).toBe(true);
      expect(result.current.voiceState).toBe("idle");
      expect(result.current.transcript).toBe("");
      expect(result.current.error).toBe(null);
    });

    it("should handle missing API key", async () => {
      vi.stubEnv("NEXT_PUBLIC_DEEPGRAM_API_KEY", "");

      const { result } = renderHook(() => useDeepgramVoice());

      await waitFor(() => {
        expect(result.current.error).toBe("Deepgram API key is required");
        expect(result.current.connectionState).toBe("error");
        expect(result.current.isConnected).toBe(false);
      });

      // Restore API key for other tests
      vi.stubEnv("NEXT_PUBLIC_DEEPGRAM_API_KEY", mockApiKey);
    });
  });

  describe("Recording Controls", () => {
    it("should start recording successfully", async () => {
      const { result } = renderHook(() => useDeepgramVoice());

      await act(async () => {
        await result.current.startRecording();
      });

      expect(mockStartVoiceRecording).toHaveBeenCalled();
      expect(result.current.error).toBe(null);
    });

    it("should stop recording successfully", async () => {
      const { result } = renderHook(() => useDeepgramVoice());

      await act(async () => {
        await result.current.stopRecording();
      });

      expect(mockStopVoiceRecording).toHaveBeenCalled();
      expect(result.current.error).toBe(null);
    });
  });

  describe("Mock Verification", () => {
    it("should use mocked service", () => {
      const { result } = renderHook(() => useDeepgramVoice());

      // Just check that the hook initializes without error
      expect(result.current).toBeDefined();
    });
  });
});
