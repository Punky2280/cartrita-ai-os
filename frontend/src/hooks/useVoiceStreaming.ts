// 2025 Voice Streaming Hook - Combines Deepgram Voice Agent with real-time WebSocket infrastructure
// Provides sub-300ms voice response with real-time collaboration features

import { useState, useEffect, useRef, useCallback } from "react";
import {
  RealtimeService,
  VoiceStreamEvent,
  RealtimeTranscription,
  RealtimeAgentResponse,
} from "../services/realtime/socket";
import { useDeepgramVoice, UseDeepgramVoiceOptions } from "./useDeepgramVoice";
import {
  VoiceAgentConfig,
  AgentUtterance,
  VoiceAnalytics,
} from "../services/deepgram";

export interface VoiceStreamingOptions extends UseDeepgramVoiceOptions {
  wsUrl?: string;
  token?: string;
  enableRealtime?: boolean;
  sessionId?: string;
}

export interface VoiceStreamingReturn {
  // Inherit all Deepgram Voice functionality
  isRecording: boolean;
  isConnected: boolean;
  voiceState:
    | "idle"
    | "recording"
    | "processing"
    | "listening"
    | "thinking"
    | "speaking"
    | "error";
  transcript: string;
  analytics: VoiceAnalytics | null;
  error: string | null;

  // Voice Agent functionality
  isAgentActive: boolean;
  agentUtterances: AgentUtterance[];
  isThinking: boolean;
  sessionId: string | null;

  // Real-time streaming functionality
  isStreamConnected: boolean;
  streamParticipants: string[];
  realtimeTranscriptions: RealtimeTranscription[];

  // Actions
  startVoiceAgent: (config?: VoiceAgentConfig) => Promise<void>;
  stopVoiceAgent: () => Promise<void>;
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<void>;
  startStreaming: (sessionId?: string) => Promise<void>;
  stopStreaming: () => Promise<void>;

  // Connection management
  reconnectStream: () => void;
  leaveSession: () => void;
}

export const useVoiceStreaming = (
  options: VoiceStreamingOptions = {},
): VoiceStreamingReturn => {
  const {
    wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:3001",
    token,
    enableRealtime = true,
    sessionId: initialSessionId,
    ...deepgramOptions
  } = options;

  // State for real-time streaming
  const [isStreamConnected, setIsStreamConnected] = useState(false);
  const [streamParticipants, setStreamParticipants] = useState<string[]>([]);
  const [realtimeTranscriptions, setRealtimeTranscriptions] = useState<
    RealtimeTranscription[]
  >([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(
    initialSessionId || null,
  );

  // Refs
  const realtimeServiceRef = useRef<RealtimeService | null>(null);

  // Use the enhanced Deepgram voice hook
  const deepgramVoice = useDeepgramVoice(deepgramOptions);

  // Initialize real-time service
  useEffect(() => {
    if (enableRealtime) {
      realtimeServiceRef.current = new RealtimeService(wsUrl, token);

      // Setup connection event handlers
      realtimeServiceRef.current.onConnect(() => {
        setIsStreamConnected(true);
        console.log("Voice streaming connected");
      });

      realtimeServiceRef.current.onDisconnect(() => {
        setIsStreamConnected(false);
        console.log("Voice streaming disconnected");
      });

      realtimeServiceRef.current.onError((error) => {
        console.error("Voice streaming error:", error);
        setIsStreamConnected(false);
      });

      // Setup voice streaming event handlers
      realtimeServiceRef.current.onVoiceTranscription((transcription) => {
        setRealtimeTranscriptions((prev) => [...prev, transcription]);
      });

      realtimeServiceRef.current.onAgentResponse((response) => {
        // Agent responses are handled by the Deepgram hook
        console.log("Received agent response via stream:", response);
      });

      realtimeServiceRef.current.onVoiceStream((event) => {
        handleVoiceStreamEvent(event);
      });
    }

    return () => {
      if (realtimeServiceRef.current) {
        realtimeServiceRef.current.disconnect();
      }
    };
  }, [enableRealtime, wsUrl, token]);

  // Handle voice stream events
  const handleVoiceStreamEvent = useCallback(
    (event: VoiceStreamEvent) => {
      switch (event.type) {
        case "session_start":
          setCurrentSessionId(event.sessionId);
          break;
        case "session_end":
          if (event.sessionId === currentSessionId) {
            setCurrentSessionId(null);
            setStreamParticipants([]);
            setRealtimeTranscriptions([]);
          }
          break;
        case "transcription":
          // Handled by onVoiceTranscription
          break;
        case "agent_response":
          // Handled by onAgentResponse
          break;
        case "agent_thinking":
          // Already handled by Deepgram hook
          break;
      }
    },
    [currentSessionId],
  );

  // Start voice streaming session
  const startStreaming = useCallback(
    async (sessionId?: string) => {
      if (!realtimeServiceRef.current || !enableRealtime) {
        throw new Error("Real-time service not available");
      }

      const sid =
        sessionId ||
        `voice_session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      setCurrentSessionId(sid);
      realtimeServiceRef.current.startVoiceSession(sid);
      // No return (void) to satisfy interface
    },
    [enableRealtime],
  );

  // Stop voice streaming session
  const stopStreaming = useCallback(async () => {
    if (realtimeServiceRef.current && currentSessionId) {
      realtimeServiceRef.current.endVoiceSession(currentSessionId);
      setCurrentSessionId(null);
      setStreamParticipants([]);
      setRealtimeTranscriptions([]);
    }
  }, [currentSessionId]);

  // Enhanced voice agent start that includes streaming
  const startVoiceAgent = useCallback(
    async (config?: VoiceAgentConfig) => {
      // Start the Deepgram voice agent
      await deepgramVoice.startVoiceAgent(config);

      // Start real-time streaming if enabled
      if (enableRealtime && !currentSessionId) {
        await startStreaming();
      }
    },
    [
      deepgramVoice.startVoiceAgent,
      enableRealtime,
      currentSessionId,
      startStreaming,
    ],
  );

  // Enhanced voice agent stop that includes streaming cleanup
  const stopVoiceAgent = useCallback(async () => {
    // Stop the Deepgram voice agent
    await deepgramVoice.stopVoiceAgent();

    // Stop streaming session
    if (currentSessionId) {
      await stopStreaming();
    }
  }, [deepgramVoice.stopVoiceAgent, currentSessionId, stopStreaming]);

  // Reconnect stream
  const reconnectStream = useCallback(() => {
    if (realtimeServiceRef.current) {
      realtimeServiceRef.current.reconnect();
    }
  }, []);

  // Leave current session
  const leaveSession = useCallback(() => {
    stopStreaming();
  }, [stopStreaming]);

  return {
    // Inherit all Deepgram Voice functionality
    isRecording: deepgramVoice.isRecording,
    isConnected: deepgramVoice.isConnected,
    voiceState: deepgramVoice.voiceState,
    transcript: deepgramVoice.transcript,
    analytics: deepgramVoice.analytics,
    error: deepgramVoice.error,

    // Voice Agent functionality
    isAgentActive: deepgramVoice.isAgentActive,
    agentUtterances: deepgramVoice.agentUtterances,
    isThinking: deepgramVoice.isThinking,
    sessionId: currentSessionId || deepgramVoice.sessionId,

    // Real-time streaming functionality
    isStreamConnected,
    streamParticipants,
    realtimeTranscriptions,

    // Enhanced actions
    startVoiceAgent,
    stopVoiceAgent,
    startRecording: deepgramVoice.startRecording,
    stopRecording: deepgramVoice.stopRecording,
    startStreaming,
    stopStreaming,

    // Connection management
    reconnectStream,
    leaveSession,
  };
};
