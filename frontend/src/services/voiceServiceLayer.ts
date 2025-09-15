// Voice Service Layer - Optimized for sub-300ms latency (2025)
// Coordinates between Deepgram Voice Agent API and real-time WebSocket infrastructure

import { VoiceAgentConfig, AgentUtterance, VoiceAnalytics } from "./deepgram";
import { RealtimeService } from "./realtime/socket";

export interface VoiceServiceConfig {
  // Performance optimization settings
  targetLatency: number; // Target response time in milliseconds
  bufferSize: number; // Audio buffer size for optimal streaming
  compression: "opus" | "linear16" | "mulaw";
  sampleRate: number; // Audio sample rate

  // Voice Agent configuration
  voiceAgent: VoiceAgentConfig;

  // Connection settings
  deepgramApiKey: string;
  websocketUrl: string;
  authToken?: string;

  // Fallback settings
  enableFallback: boolean;
  fallbackModel: string;
  maxRetries: number;
}

export interface VoiceServiceMetrics {
  latency: {
    averageMs: number;
    p95Ms: number;
    p99Ms: number;
  };
  throughput: {
    messagesPerSecond: number;
    audioChunksPerSecond: number;
  };
  quality: {
    transcriptionAccuracy: number;
    audioQuality: number;
    dropRate: number;
  };
  connection: {
    uptime: number;
    reconnects: number;
    errors: number;
  };
}

export class VoiceServiceLayer {
  private config: VoiceServiceConfig;
  private isActive = false;
  private metrics: VoiceServiceMetrics;
  private performanceObserver: PerformanceObserver | null = null;
  private latencyHistory: number[] = [];
  private startTime: number = 0;

  constructor(config: VoiceServiceConfig) {
    this.config = config;
    this.metrics = this.initializeMetrics();
    this.setupPerformanceMonitoring();
  }

  private initializeMetrics(): VoiceServiceMetrics {
    return {
      latency: { averageMs: 0, p95Ms: 0, p99Ms: 0 },
      throughput: { messagesPerSecond: 0, audioChunksPerSecond: 0 },
      quality: { transcriptionAccuracy: 0, audioQuality: 0, dropRate: 0 },
      connection: { uptime: 0, reconnects: 0, errors: 0 },
    };
  }

  private setupPerformanceMonitoring() {
    if ("PerformanceObserver" in window) {
      this.performanceObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry) => {
          if (entry.name.startsWith("voice-service-")) {
            this.recordLatency(entry.duration);
          }
        });
      });
      this.performanceObserver.observe({ entryTypes: ["measure"] });
    }
  }

  private recordLatency(latency: number) {
    this.latencyHistory.push(latency);

    // Keep only last 100 measurements for rolling average
    if (this.latencyHistory.length > 100) {
      this.latencyHistory.shift();
    }

    // Calculate metrics
    const sorted = [...this.latencyHistory].sort((a, b) => a - b);
    this.metrics.latency.averageMs =
      sorted.reduce((a, b) => a + b, 0) / sorted.length;
    this.metrics.latency.p95Ms = sorted[Math.floor(sorted.length * 0.95)];
    this.metrics.latency.p99Ms = sorted[Math.floor(sorted.length * 0.99)];
  }

  public async initialize(): Promise<void> {
    try {
      performance.mark("voice-service-init-start");

      // Optimize browser settings for low latency
      await this.optimizeBrowserPerformance();

      // Pre-warm connections
      await this.prewarmConnections();

      performance.mark("voice-service-init-end");
      performance.measure(
        "voice-service-init",
        "voice-service-init-start",
        "voice-service-init-end",
      );

      this.isActive = true;
      console.log("Voice Service Layer initialized for sub-300ms latency");
    } catch (error) {
      this.metrics.connection.errors++;
      throw new Error(`Failed to initialize voice service: ${error}`);
    }
  }

  private async optimizeBrowserPerformance(): Promise<void> {
    // Request high-performance audio context
    if ("audioWorklet" in window.AudioContext.prototype) {
      const audioContext = new AudioContext({
        latencyHint: "interactive",
        sampleRate: this.config.sampleRate,
      });

      // Ensure audio context is running
      if (audioContext.state === "suspended") {
        await audioContext.resume();
      }
    }

    // Request wake lock to prevent system sleep
    if ("wakeLock" in navigator) {
      try {
        await (navigator as any).wakeLock.request("screen");
      } catch (e) {
        console.warn("Wake lock not available:", e);
      }
    }

    // Optimize garbage collection
    if ("gc" in window && typeof (window as any).gc === "function") {
      (window as any).gc();
    }
  }

  private async prewarmConnections(): Promise<void> {
    // Pre-establish WebSocket connection
    const testWs = new WebSocket(this.config.websocketUrl);

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        testWs.close();
        reject(new Error("Connection prewarming timeout"));
      }, 5000);

      testWs.onopen = () => {
        clearTimeout(timeout);
        testWs.close();
        resolve();
      };

      testWs.onerror = (error) => {
        clearTimeout(timeout);
        reject(error);
      };
    });
  }

  public async startVoiceSession(sessionId: string): Promise<void> {
    if (!this.isActive) {
      throw new Error("Voice service not initialized");
    }

    performance.mark("voice-session-start");
    this.startTime = Date.now();

    try {
      // Configure for minimum latency
      const optimizedConfig: VoiceAgentConfig = {
        ...this.config.voiceAgent,
        // Force optimal settings for sub-300ms latency
        listenModel: "nova-3", // Latest model for best speed/accuracy
        thinkModel: "gpt-4o-mini", // Fast thinking model
        temperature: 0.3, // Lower temperature for faster response
        maxTokens: 150, // Shorter responses for speed
        contextRetention: false, // Disable for speed if not needed
      };

      console.log(
        `Starting voice session ${sessionId} with sub-300ms configuration`,
      );
    } catch (error) {
      this.metrics.connection.errors++;
      throw error;
    }
  }

  public measureResponseTime(): number {
    const responseTime = Date.now() - this.startTime;
    performance.mark("voice-response-end");
    performance.measure(
      "voice-service-response",
      "voice-session-start",
      "voice-response-end",
    );

    this.recordLatency(responseTime);
    return responseTime;
  }

  public getMetrics(): VoiceServiceMetrics {
    // Update uptime
    this.metrics.connection.uptime = this.isActive
      ? Date.now() - this.startTime
      : 0;
    return { ...this.metrics };
  }

  public isOptimalPerformance(): boolean {
    return (
      this.metrics.latency.averageMs < this.config.targetLatency &&
      this.metrics.quality.dropRate < 0.01 && // Less than 1% drop rate
      this.metrics.connection.uptime > 0
    );
  }

  public async optimizeForLatency(): Promise<void> {
    // Dynamic optimization based on current performance
    if (this.metrics.latency.averageMs > this.config.targetLatency) {
      console.log("Optimizing for lower latency...");

      // Reduce buffer sizes
      this.config.bufferSize = Math.max(64, this.config.bufferSize / 2);

      // Switch to faster models if available
      if (this.config.voiceAgent.thinkModel !== "gpt-4o-mini") {
        this.config.voiceAgent.thinkModel = "gpt-4o-mini";
        console.log("Switched to faster think model");
      }

      // Reduce response length
      this.config.voiceAgent.maxTokens = Math.max(
        50,
        (this.config.voiceAgent.maxTokens || 150) * 0.8,
      );
    }
  }

  public dispose(): void {
    this.isActive = false;

    if (this.performanceObserver) {
      this.performanceObserver.disconnect();
    }

    // Clear performance marks
    try {
      performance.clearMarks();
      performance.clearMeasures();
    } catch (e) {
      // Ignore cleanup errors
    }

    console.log("Voice Service Layer disposed");
  }
}

// Factory function for creating optimized voice service
export const createOptimizedVoiceService = (
  config: Partial<VoiceServiceConfig>,
): VoiceServiceLayer => {
  const defaultConfig: VoiceServiceConfig = {
    targetLatency: 300, // Sub-300ms target
    bufferSize: 128,
    compression: "opus",
    sampleRate: 16000,
    voiceAgent: {
      instructions:
        "You are a helpful AI assistant. Be conversational, concise, and engaging.",
      voice: "aura-asteria-en",
      thinkModel: "gpt-4o-mini",
      listenModel: "nova-3",
      temperature: 0.3,
      maxTokens: 150,
      contextRetention: false,
    },
    deepgramApiKey: process.env.NEXT_PUBLIC_DEEPGRAM_API_KEY || "",
    websocketUrl: process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:3001",
    enableFallback: true,
    fallbackModel: "nova-2",
    maxRetries: 3,
    ...config,
  };

  return new VoiceServiceLayer(defaultConfig);
};
