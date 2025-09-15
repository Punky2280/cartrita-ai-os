// Cartrita AI OS - Voice Output Hook
// Advanced TTS state management and controls

import { useState, useRef, useEffect, useCallback } from "react";
import { useVoice } from "@/hooks";
import type { VoiceSettings } from "@/types";

export interface VoiceOutputState {
  isPlaying: boolean;
  isMuted: boolean;
  volume: number;
  speed: number;
  selectedVoice: string;
  currentText: string;
  playbackProgress: number;
  voiceState:
    | "idle"
    | "recording"
    | "processing"
    | "listening"
    | "thinking"
    | "speaking"
    | "error";
}

export interface VoiceOutputActions {
  speak: (text: string) => Promise<void>;
  stop: () => void;
  toggleMute: () => void;
  setVolume: (volume: number) => void;
  setSpeed: (speed: number) => void;
  setVoice: (voiceId: string) => void;
  testVoice: () => Promise<void>;
}

export interface UseVoiceOutputOptions {
  defaultVoice?: string;
  defaultVolume?: number;
  defaultSpeed?: number;
  onVoiceStart?: () => void;
  onVoiceEnd?: () => void;
  onError?: (error: Error) => void;
}

export interface UseVoiceOutputReturn
  extends VoiceOutputState,
    VoiceOutputActions {}

export function useVoiceOutput(
  options: UseVoiceOutputOptions = {},
): UseVoiceOutputReturn {
  const {
    defaultVoice = "aura-asteria-en",
    defaultVolume = 80,
    defaultSpeed = 1.0,
    onVoiceStart,
    onVoiceEnd,
    onError,
  } = options;

  // Voice service integration
  const { speak: voiceSpeak, isSpeaking, voiceState } = useVoice();

  // Component state
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [volume, setVolumeState] = useState(defaultVolume);
  const [speed, setSpeedState] = useState(defaultSpeed);
  const [selectedVoice, setSelectedVoice] = useState(defaultVoice);
  const [currentText, setCurrentText] = useState("");
  const [playbackProgress, setPlaybackProgress] = useState(0);

  // Refs
  const playbackTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const gainNodeRef = useRef<GainNode | null>(null);

  // Initialize audio context
  useEffect(() => {
    try {
      audioContextRef.current = new AudioContext();
      gainNodeRef.current = audioContextRef.current.createGain();
      gainNodeRef.current.connect(audioContextRef.current.destination);
    } catch (error) {
      console.error("Failed to initialize audio context:", error);
      onError?.(error as Error);
    }

    return () => {
      if (audioContextRef.current) {
        void void audioContextRef.current.close();
      }
      if (playbackTimeoutRef.current) {
        clearTimeout(playbackTimeoutRef.current);
      }
    };
  }, [onError]);

  // Update volume when it changes
  useEffect(() => {
    if (gainNodeRef.current) {
      const actualVolume = isMuted ? 0 : volume / 100;
      gainNodeRef.current.gain.setValueAtTime(
        actualVolume,
        audioContextRef.current?.currentTime || 0,
      );
    }
  }, [volume, isMuted]);

  // Speak function with progress tracking
  const speak = useCallback(
    async (text: string) => {
      if (!text.trim()) {
        throw new Error("Text is required for speech synthesis");
      }

      try {
        setIsPlaying(true);
        setCurrentText(text);
        setPlaybackProgress(0);
        onVoiceStart?.();

        // Use the voice service
        await voiceSpeak(text);

        // Simulate progress for UI feedback
        const duration = Math.max(text.length * 50, 1000); // Rough estimate
        const interval = 100;
        const steps = duration / interval;
        let currentStep = 0;

        const progressInterval = setInterval(() => {
          currentStep++;
          setPlaybackProgress((currentStep / steps) * 100);

          if (currentStep >= steps) {
            clearInterval(progressInterval);
          }
        }, interval);

        playbackTimeoutRef.current = setTimeout(() => {
          clearInterval(progressInterval);
          setIsPlaying(false);
          setPlaybackProgress(100);
          onVoiceEnd?.();
        }, duration);
      } catch (error) {
        console.error("Voice output error:", error);
        setIsPlaying(false);
        setPlaybackProgress(0);
        onError?.(error as Error);
        throw error;
      }
    },
    [voiceSpeak, onVoiceStart, onVoiceEnd, onError],
  );

  // Stop playback
  const stop = useCallback(() => {
    if (playbackTimeoutRef.current) {
      clearTimeout(playbackTimeoutRef.current);
    }
    setIsPlaying(false);
    setPlaybackProgress(0);
    onVoiceEnd?.();
  }, [onVoiceEnd]);

  // Toggle mute
  const toggleMute = useCallback(() => {
    setIsMuted((prev) => !prev);
  }, []);

  // Set volume with validation
  const setVolume = useCallback((newVolume: number) => {
    const clampedVolume = Math.max(0, Math.min(100, newVolume));
    setVolumeState(clampedVolume);
  }, []);

  // Set speed with validation
  const setSpeed = useCallback((newSpeed: number) => {
    const clampedSpeed = Math.max(0.5, Math.min(2.0, newSpeed));
    setSpeedState(clampedSpeed);
  }, []);

  // Set voice
  const setVoice = useCallback((voiceId: string) => {
    setSelectedVoice(voiceId);
  }, []);

  // Test voice with sample text
  const testVoice = useCallback(async () => {
    const testText =
      "Hello! This is a test of the voice output system using Deepgram TTS.";
    await speak(testText);
  }, [speak]);

  return {
    // State
    isPlaying,
    isMuted,
    volume,
    speed,
    selectedVoice,
    currentText,
    playbackProgress,
    voiceState,

    // Actions
    speak,
    stop,
    toggleMute,
    setVolume,
    setSpeed,
    setVoice,
    testVoice,
  };
}

export default useVoiceOutput;
