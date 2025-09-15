// Enhanced Socket.IO client for real-time events and 2025 Voice Agent streaming
import { io, Socket } from "socket.io-client";
import {
  VoiceTranscription,
  AgentUtterance,
  VoiceAnalytics,
} from "../deepgram";

export interface PresenceEvent {
  userId: string;
  status: "online" | "offline" | "away";
  lastActive?: string;
}

export interface TypingEvent {
  conversationId: string;
  userId: string;
  isTyping: boolean;
}

// 2025 Voice Agent streaming events
export interface VoiceStreamEvent {
  sessionId: string;
  userId: string;
  type:
    | "audio_chunk"
    | "transcription"
    | "agent_response"
    | "agent_thinking"
    | "session_start"
    | "session_end";
  data: any;
  timestamp: number;
}

export interface AudioStreamChunk {
  sessionId: string;
  chunk: ArrayBuffer | Blob;
  sequence: number;
  isEnd: boolean;
}

export interface RealtimeTranscription extends VoiceTranscription {
  sessionId: string;
  userId: string;
}

export interface RealtimeAgentResponse extends AgentUtterance {
  sessionId: string;
  targetUserId?: string;
}

export class RealtimeService {
  private socket: Socket;
  private currentSessionId: string | null = null;

  constructor(url: string, token?: string) {
    this.socket = io(url, {
      transports: ["websocket"],
      auth: token ? { token } : undefined,
      autoConnect: true,
    });
  }

  // Existing presence and typing functionality
  onPresence(cb: (event: PresenceEvent) => void) {
    this.socket.on("presence", cb);
  }

  onTyping(cb: (event: TypingEvent) => void) {
    this.socket.on("typing", cb);
  }

  emitTyping(conversationId: string, isTyping: boolean) {
    this.socket.emit("typing", { conversationId, isTyping });
  }

  // 2025 Voice Agent streaming methods
  startVoiceSession(sessionId: string) {
    this.currentSessionId = sessionId;
    this.socket.emit("voice:session:start", { sessionId });
  }

  endVoiceSession(sessionId?: string) {
    const sid = sessionId || this.currentSessionId;
    if (sid) {
      this.socket.emit("voice:session:end", { sessionId: sid });
      this.currentSessionId = null;
    }
  }

  streamAudioChunk(chunk: AudioStreamChunk) {
    if (this.currentSessionId) {
      this.socket.emit("voice:audio:chunk", chunk);
    }
  }

  onVoiceTranscription(cb: (transcription: RealtimeTranscription) => void) {
    this.socket.on("voice:transcription", cb);
  }

  onAgentResponse(cb: (response: RealtimeAgentResponse) => void) {
    this.socket.on("voice:agent:response", cb);
  }

  onAgentThinking(
    cb: (data: {
      sessionId: string;
      isThinking: boolean;
      progress?: number;
    }) => void,
  ) {
    this.socket.on("voice:agent:thinking", cb);
  }

  onVoiceAnalytics(
    cb: (analytics: VoiceAnalytics & { sessionId: string }) => void,
  ) {
    this.socket.on("voice:analytics", cb);
  }

  onVoiceStream(cb: (event: VoiceStreamEvent) => void) {
    this.socket.on("voice:stream", cb);
  }

  // Connection management
  isConnected(): boolean {
    return this.socket.connected;
  }

  reconnect() {
    this.socket.connect();
  }

  disconnect() {
    if (this.currentSessionId) {
      this.endVoiceSession();
    }
    this.socket.disconnect();
  }

  // Connection event handlers
  onConnect(cb: () => void) {
    this.socket.on("connect", cb);
  }

  onDisconnect(cb: () => void) {
    this.socket.on("disconnect", cb);
  }

  onError(cb: (error: any) => void) {
    this.socket.on("error", cb);
  }
}

// Usage example (in a React hook or service):
// const rts = new RealtimeService(process.env.NEXT_PUBLIC_WS_URL, token)
// rts.onPresence(...)
// rts.onTyping(...)
// rts.emitTyping(conversationId, true)
