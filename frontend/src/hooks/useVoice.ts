// Cartrita AI OS - Voice Hook Integration
// Real implementation with advanced voice capabilities

import { useState, useEffect, useCallback, useRef } from "react";
import DeepgramVoiceService, {
  VoiceState,
  VoiceTranscription,
  VoiceAnalytics,
  ConversationMetrics,
  DeepgramConfig,
} from "@/services/deepgram";

export interface UseVoiceOptions extends Partial<DeepgramConfig> {
  autoStart?: boolean;
  enableAnalytics?: boolean;
  enableMetrics?: boolean;
  onTranscription?: (transcription: VoiceTranscription) => void;
  onResponse?: (response: string) => void;
  onError?: (error: unknown) => void;
}

export interface VoiceCapabilities {
  // Core voice functions
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<void>;
  speak: (text: string) => Promise<void>;

  // Voice Agent functions
  startVoiceAgent: (systemPrompt?: string) => Promise<void>;
  stopVoiceAgent: () => void;
  sendVoiceMessage: (audioBlob: Blob) => Promise<void>;

  // State management
  voiceState: VoiceState;
  isRecording: boolean;
  isProcessing: boolean;
  isSpeaking: boolean;

  // Transcription and analytics
  currentTranscription: string;
  finalTranscription: string;
  analytics: VoiceAnalytics | null;
  metrics: ConversationMetrics | null;

  // Voice quality metrics
  audioLevel: number;
  signalQuality: "excellent" | "good" | "fair" | "poor";

  // Configuration
  updateConfig: (config: Partial<DeepgramConfig>) => void;

  // Utility functions
  toggleRecording: () => Promise<void>;
  clearTranscriptions: () => void;
  getRecordingDuration: () => number;
}

export function useVoice(options: UseVoiceOptions = {}): VoiceCapabilities {
  // State management
  const [voiceState, setVoiceState] = useState<VoiceState>("idle");
  const [currentTranscription, setCurrentTranscription] = useState("");
  const [finalTranscription, setFinalTranscription] = useState("");
  const [analytics, setAnalytics] = useState<VoiceAnalytics | null>(null);
  const [metrics, setMetrics] = useState<ConversationMetrics | null>(null);
  const [audioLevel, setAudioLevel] = useState(0);
  const [signalQuality, setSignalQuality] = useState<
    "excellent" | "good" | "fair" | "poor"
  >("good");

  // Refs
  const voiceServiceRef = useRef<DeepgramVoiceService | null>(null);
  const voiceAgentWsRef = useRef<WebSocket | null>(null);
  const recordingStartTimeRef = useRef<number | null>(null);
  const audioAnalyzerRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  // Get API key from environment
  const apiKey =
    process.env.NEXT_PUBLIC_DEEPGRAM_API_KEY ||
    process.env.DEEPGRAM_API_KEY ||
    "";

  // Initialize voice service
  useEffect(() => {
    if (!apiKey) {
      console.error("Deepgram API key is required");
      return;
    }

    const config: DeepgramConfig = {
      apiKey,
      model: options.model || "nova-2",
      language: options.language || "en-US",
      smartFormat: options.smartFormat ?? true,
      punctuate: options.punctuate ?? true,
      interim_results: options.interim_results ?? true,
      endpointing: options.endpointing || 300,
    };

    voiceServiceRef.current = new DeepgramVoiceService(config);

    // Setup event listeners
    voiceServiceRef.current.on(
      "stateChange",
      ({ state }: { state: VoiceState }) => {
        setVoiceState(state);
      },
    );

    voiceServiceRef.current.on(
      "transcription",
      (transcription: VoiceTranscription) => {
        if (transcription.is_final) {
          setFinalTranscription((prev) => prev + " " + transcription.text);
          setCurrentTranscription("");
          options.onTranscription?.(transcription);
        } else {
          setCurrentTranscription(transcription.text);
        }
      },
    );

    voiceServiceRef.current.on("analytics", (analytics: VoiceAnalytics) => {
      if (options.enableAnalytics) {
        setAnalytics(analytics);
      }
    });

    voiceServiceRef.current.on(
      "metrics",
      (metrics: Partial<ConversationMetrics>) => {
        if (options.enableMetrics) {
          setMetrics(
            (prev) => ({ ...prev, ...metrics }) as ConversationMetrics,
          );
        }
      },
    );

    voiceServiceRef.current.on("response", (response: string) => {
      options.onResponse?.(response);
    });

    voiceServiceRef.current.on("error", (error: unknown) => {
      console.error("Voice service error:", error);
      options.onError?.(error);
    });

    // Cleanup on unmount
    return () => {
      if (voiceServiceRef.current) {
        voiceServiceRef.current.disconnect();
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [apiKey, options]);

  // Audio level monitoring
  const setupAudioLevelMonitoring = useCallback(
    (stream: MediaStream) => {
      const audioContext = new AudioContext();
      const source = audioContext.createMediaStreamSource(stream);
      const analyzer = audioContext.createAnalyser();

      analyzer.fftSize = 256;
      source.connect(analyzer);
      audioAnalyzerRef.current = analyzer;

      const dataArray = new Uint8Array(analyzer.frequencyBinCount);

      const updateAudioLevel = () => {
        if (audioAnalyzerRef.current) {
          audioAnalyzerRef.current.getByteFrequencyData(dataArray);

          // Calculate average audio level
          const average =
            dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;
          setAudioLevel(average);

          // Determine signal quality based on audio level and consistency
          if (average > 80) {
            setSignalQuality("excellent");
          } else if (average > 50) {
            setSignalQuality("good");
          } else if (average > 20) {
            setSignalQuality("fair");
          } else {
            setSignalQuality("poor");
          }
        }

        if (voiceState === "recording") {
          animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
        }
      };

      updateAudioLevel();
    },
    [voiceState],
  );

  // Core voice functions
  const startRecording = useCallback(async () => {
    try {
      if (!voiceServiceRef.current) {
        throw new Error("Voice service not initialized");
      }

      recordingStartTimeRef.current = Date.now();
      await voiceServiceRef.current.startVoiceRecording();

      // Setup audio level monitoring
      if (voiceServiceRef.current.isCurrentlyRecording()) {
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: true,
        });
        setupAudioLevelMonitoring(stream);
      }
    } catch (error) {
      console.error("Failed to start recording:", error);
      throw error;
    }
  }, [setupAudioLevelMonitoring]);

  const stopRecording = useCallback(async () => {
    try {
      if (voiceServiceRef.current) {
        await voiceServiceRef.current.stopVoiceRecording();
      }

      recordingStartTimeRef.current = null;

      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
    } catch (error) {
      console.error("Failed to stop recording:", error);
      throw error;
    }
  }, []);

  const speak = useCallback(async (text: string) => {
    try {
      if (!voiceServiceRef.current) {
        throw new Error("Voice service not initialized");
      }

      await voiceServiceRef.current.synthesizeSpeech(text);
    } catch (error) {
      console.error("Failed to speak:", error);
      throw error;
    }
  }, []);

  // Voice Agent functions
  const startVoiceAgent = useCallback(async (systemPrompt?: string) => {
    try {
      if (!voiceServiceRef.current) {
        throw new Error("Voice service not initialized");
      }

      const voiceAgentWs = await voiceServiceRef.current.startVoiceAgent({
        instructions:
          systemPrompt ||
          "You are a helpful AI assistant with natural conversation abilities.",
        maxTokens: 2000,
        voice: "aura-asteria-en",
        thinkModel: "gpt-4o-mini",
        listenModel: "nova-3",
      });

      voiceAgentWsRef.current = voiceAgentWs;
      recordingStartTimeRef.current = Date.now();
    } catch (error) {
      console.error("Failed to start voice agent:", error);
      throw error;
    }
  }, []);

  const stopVoiceAgent = useCallback(() => {
    if (voiceAgentWsRef.current) {
      voiceAgentWsRef.current.close();
      voiceAgentWsRef.current = null;
    }
    recordingStartTimeRef.current = null;
  }, []);

  const sendVoiceMessage = useCallback(async (audioBlob: Blob) => {
    try {
      if (!voiceAgentWsRef.current) {
        throw new Error("Voice agent not connected");
      }

      // Convert audio blob to base64 and send
      const arrayBuffer = await audioBlob.arrayBuffer();
      const base64Audio = btoa(
        String.fromCharCode(...new Uint8Array(arrayBuffer)),
      );

      voiceAgentWsRef.current.send(
        JSON.stringify({
          type: "audio",
          audio: base64Audio,
          encoding: "webm",
        }),
      );
    } catch (error) {
      console.error("Failed to send voice message:", error);
      throw error;
    }
  }, []);

  // Utility functions
  const toggleRecording = useCallback(async () => {
    if (voiceState === "recording") {
      await stopRecording();
    } else if (voiceState === "idle") {
      await startRecording();
    }
  }, [voiceState, startRecording, stopRecording]);

  const clearTranscriptions = useCallback(() => {
    setCurrentTranscription("");
    setFinalTranscription("");
  }, []);

  const getRecordingDuration = useCallback(() => {
    if (recordingStartTimeRef.current) {
      return Date.now() - recordingStartTimeRef.current;
    }
    return 0;
  }, []);

  const updateConfig = useCallback((config: Partial<DeepgramConfig>) => {
    // This would reinitialize the service with new config
    // For now, we'll just log the config change
    console.log("Voice config updated:", config);
  }, []);

  // Computed values
  const isRecording = voiceState === "recording";
  const isProcessing = voiceState === "processing";
  const isSpeaking = voiceState === "speaking";

  return {
    // Core voice functions
    startRecording,
    stopRecording,
    speak,

    // Voice Agent functions
    startVoiceAgent,
    stopVoiceAgent,
    sendVoiceMessage,

    // State management
    voiceState,
    isRecording,
    isProcessing,
    isSpeaking,

    // Transcription and analytics
    currentTranscription,
    finalTranscription,
    analytics,
    metrics,

    // Voice quality metrics
    audioLevel,
    signalQuality,

    // Configuration
    updateConfig,

    // Utility functions
    toggleRecording,
    clearTranscriptions,
    getRecordingDuration,
  };
}
