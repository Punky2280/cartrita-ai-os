// Cartrita AI OS - Audio Analysis Hook Tests
// Comprehensive tests for real-time frequency analysis

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useAudioAnalysis } from "../useAudioAnalysis";

// Mock MediaDevices
const mockGetUserMedia = vi.fn();
Object.defineProperty(navigator, "mediaDevices", {
  value: {
    getUserMedia: mockGetUserMedia,
  },
  writable: true,
});

// Mock AudioContext
const mockAnalyser = {
  fftSize: 2048,
  frequencyBinCount: 1024,
  smoothingTimeConstant: 0.8,
  minDecibels: -90,
  maxDecibels: -10,
  getByteFrequencyData: vi.fn(),
  getByteTimeDomainData: vi.fn(),
  connect: vi.fn(),
};

const mockMediaStreamSource = {
  connect: vi.fn(),
  disconnect: vi.fn(),
};

const mockAudioContext = {
  createAnalyser: vi.fn(() => mockAnalyser),
  createMediaStreamSource: vi.fn(() => mockMediaStreamSource),
  close: vi.fn(),
  state: "running",
  sampleRate: 44100,
};

const mockMediaStream = {
  getTracks: () => [{ stop: vi.fn() }],
};

// Mock window.AudioContext
Object.defineProperty(window, "AudioContext", {
  value: vi.fn(() => mockAudioContext),
  writable: true,
});

describe("useAudioAnalysis", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetUserMedia.mockResolvedValue(mockMediaStream);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("Initialization", () => {
    it("should initialize with default state", () => {
      const { result } = renderHook(() => useAudioAnalysis());

      expect(result.current.analysisData).toBe(null);
      expect(result.current.isAnalyzing).toBe(false);
      expect(result.current.error).toBe(null);
    });

    it("should accept custom configuration", () => {
      const customConfig = {
        fftSize: 4096,
        smoothingTimeConstant: 0.5,
      };

      const { result } = renderHook(() =>
        useAudioAnalysis({ config: customConfig }),
      );

      expect(result.current.analysisData).toBe(null);
      expect(result.current.isAnalyzing).toBe(false);
    });

    it("should respect enabled flag", () => {
      const { result } = renderHook(() => useAudioAnalysis({ enabled: false }));

      expect(result.current.isAnalyzing).toBe(false);
    });
  });

  describe("Audio Analysis", () => {
    it("should start analysis with valid stream", async () => {
      const { result } = renderHook(() => useAudioAnalysis());

      await act(async () => {
        await result.current.startAnalysis(mockMediaStream as any);
      });

      expect(result.current.isAnalyzing).toBe(true);
      expect(result.current.error).toBe(null);
      expect(mockAudioContext.createAnalyser).toHaveBeenCalled();
    });

    it("should handle analysis errors", async () => {
      const mockError = new Error("Audio context failed");
      const originalAudioContext = (window as any).AudioContext;

      (window as any).AudioContext = vi.fn(() => {
        throw mockError;
      });

      const { result } = renderHook(() => useAudioAnalysis());

      await expect(
        result.current.startAnalysis(mockMediaStream as any),
      ).rejects.toThrow("Audio context failed");
      (window as any).AudioContext = originalAudioContext;
    });

    it("should stop analysis correctly", async () => {
      const { result } = renderHook(() => useAudioAnalysis());

      await act(async () => {
        await result.current.startAnalysis(mockMediaStream as any);
      });

      expect(result.current.isAnalyzing).toBe(true);

      act(() => {
        result.current.stopAnalysis();
      });

      expect(result.current.isAnalyzing).toBe(false);
      expect(result.current.analysisData).toBe(null);
      expect(mockAudioContext.close).toHaveBeenCalled();
    });
  });

  describe("Configuration Updates", () => {
    it("should update analyser configuration", async () => {
      const { result } = renderHook(() => useAudioAnalysis());

      await act(async () => {
        await result.current.startAnalysis(mockMediaStream as any);
      });

      act(() => {
        result.current.updateConfig({
          fftSize: 4096,
          smoothingTimeConstant: 0.5,
        });
      });

      expect(mockAnalyser.fftSize).toBe(4096);
      expect(mockAnalyser.smoothingTimeConstant).toBe(0.5);
    });
  });

  describe("Data Processing", () => {
    it("should process frequency and time domain data", async () => {
      // Mock analyser data
      const mockFrequencyData = new Uint8Array(1024);
      const mockTimeData = new Uint8Array(1024);

      // Fill with some test data
      for (let i = 0; i < 1024; i++) {
        mockFrequencyData[i] = Math.sin(i * 0.1) * 127 + 128;
        mockTimeData[i] = Math.sin(i * 0.05) * 127 + 128;
      }

      mockAnalyser.getByteFrequencyData.mockImplementation(
        (array: Uint8Array) => {
          array.set(mockFrequencyData);
        },
      );

      mockAnalyser.getByteTimeDomainData.mockImplementation(
        (array: Uint8Array) => {
          array.set(mockTimeData);
        },
      );

      const { result } = renderHook(() => useAudioAnalysis());

      await act(async () => {
        await result.current.startAnalysis(mockMediaStream as any);
      });

      // Wait for analysis data to be processed
      await waitFor(() => {
        expect(result.current.analysisData).not.toBe(null);
      });

      expect(result.current.analysisData).toBeDefined();
      expect(result.current.analysisData?.frequencyData).toBeInstanceOf(
        Uint8Array,
      );
      expect(result.current.analysisData?.timeData).toBeInstanceOf(Uint8Array);
      expect(typeof result.current.analysisData?.volume).toBe("number");
      expect(typeof result.current.analysisData?.dominantFrequency).toBe(
        "number",
      );
      expect(typeof result.current.analysisData?.isActive).toBe("boolean");
    });

    it("should calculate volume correctly", async () => {
      const mockTimeData = new Uint8Array(1024);
      for (let i = 0; i < 1024; i++) {
        mockTimeData[i] = 255; // Maximum amplitude
      }

      mockAnalyser.getByteFrequencyData.mockImplementation(
        (array: Uint8Array) => {
          array.set(new Uint8Array(1024));
        },
      );

      mockAnalyser.getByteTimeDomainData.mockImplementation(
        (array: Uint8Array) => {
          array.set(mockTimeData);
        },
      );

      const { result } = renderHook(() => useAudioAnalysis());

      await act(async () => {
        await result.current.startAnalysis(mockMediaStream as any);
      });

      await waitFor(() => {
        expect(result.current.analysisData).not.toBe(null);
      });

      expect(result.current.analysisData?.volume).toBeGreaterThan(0);
    });
  });

  describe("Performance", () => {
    it("should handle rapid configuration changes", async () => {
      const { result } = renderHook(() => useAudioAnalysis());

      await act(async () => {
        await result.current.startAnalysis(mockMediaStream as any);
      });

      // Rapid config updates
      for (let i = 0; i < 10; i++) {
        act(() => {
          result.current.updateConfig({
            fftSize: 2048 + i * 100,
            smoothingTimeConstant: 0.8 - i * 0.05,
          });
        });
      }

      expect(result.current.error).toBe(null);
    });
  });
});
