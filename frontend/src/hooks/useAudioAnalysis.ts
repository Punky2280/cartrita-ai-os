// Cartrita AI OS - Audio Analysis Hook
// Real-time frequency analysis for waveform visualization

import { useState, useEffect, useRef, useCallback } from "react";

export interface AudioAnalysisConfig {
  fftSize: number;
  smoothingTimeConstant: number;
  minDecibels: number;
  maxDecibels: number;
  sampleRate: number;
}

export interface AudioAnalysisData {
  frequencyData: Uint8Array;
  timeData: Uint8Array;
  volume: number;
  dominantFrequency: number;
  isActive: boolean;
}

export interface UseAudioAnalysisOptions {
  config?: Partial<AudioAnalysisConfig>;
  enabled?: boolean;
}

export interface UseAudioAnalysisReturn {
  analysisData: AudioAnalysisData | null;
  isAnalyzing: boolean;
  error: string | null;
  startAnalysis: (stream: MediaStream) => Promise<void>;
  stopAnalysis: () => void;
  updateConfig: (config: Partial<AudioAnalysisConfig>) => void;
}

const defaultConfig: AudioAnalysisConfig = {
  fftSize: 2048,
  smoothingTimeConstant: 0.8,
  minDecibels: -90,
  maxDecibels: -10,
  sampleRate: 44100,
};

export const useAudioAnalysis = (
  options: UseAudioAnalysisOptions = {},
): UseAudioAnalysisReturn => {
  const { config: userConfig = {}, enabled = true } = options;

  const [analysisData, setAnalysisData] = useState<AudioAnalysisData | null>(
    null,
  );
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const configRef = useRef<AudioAnalysisConfig>({
    ...defaultConfig,
    ...userConfig,
  });

  // Update configuration
  const updateConfig = useCallback(
    (newConfig: Partial<AudioAnalysisConfig>) => {
      configRef.current = { ...configRef.current, ...newConfig };

      if (analyserRef.current) {
        analyserRef.current.fftSize = configRef.current.fftSize;
        analyserRef.current.smoothingTimeConstant =
          configRef.current.smoothingTimeConstant;
        analyserRef.current.minDecibels = configRef.current.minDecibels;
        analyserRef.current.maxDecibels = configRef.current.maxDecibels;
      }
    },
    [],
  );

  // Calculate dominant frequency
  const calculateDominantFrequency = useCallback(
    (frequencyData: Uint8Array): number => {
      let maxIndex = 0;
      let maxValue = 0;

      for (let i = 0; i < frequencyData.length; i++) {
        if (frequencyData[i] > maxValue) {
          maxValue = frequencyData[i];
          maxIndex = i;
        }
      }

      // Convert bin index to frequency
      const nyquist = configRef.current.sampleRate / 2;
      return (maxIndex * nyquist) / frequencyData.length;
    },
    [],
  );

  // Calculate volume level
  const calculateVolume = useCallback((timeData: Uint8Array): number => {
    let sum = 0;
    for (let i = 0; i < timeData.length; i++) {
      const amplitude = (timeData[i] - 128) / 128;
      sum += amplitude * amplitude;
    }
    return Math.sqrt(sum / timeData.length);
  }, []);

  // Analysis loop
  const analyze = useCallback(() => {
    if (!analyserRef.current || !enabled) return;

    const bufferLength = analyserRef.current.frequencyBinCount;
    const frequencyData = new Uint8Array(bufferLength);
    const timeData = new Uint8Array(bufferLength);

    analyserRef.current.getByteFrequencyData(frequencyData);
    analyserRef.current.getByteTimeDomainData(timeData);

    const volume = calculateVolume(timeData);
    const dominantFrequency = calculateDominantFrequency(frequencyData);

    setAnalysisData({
      frequencyData: new Uint8Array(frequencyData),
      timeData: new Uint8Array(timeData),
      volume,
      dominantFrequency,
      isActive: volume > 0.01, // Threshold for activity detection
    });

    if (isAnalyzing) {
      animationFrameRef.current = requestAnimationFrame(analyze);
    }
  }, [enabled, isAnalyzing, calculateVolume, calculateDominantFrequency]);

  // Start analysis
  const startAnalysis = useCallback(
    async (stream: MediaStream) => {
      try {
        setError(null);

        // Create audio context
        audioContextRef.current = new (window.AudioContext ||
          (window as any).webkitAudioContext)({
          sampleRate: configRef.current.sampleRate,
        });

        // Create analyser node
        analyserRef.current = audioContextRef.current.createAnalyser();
        analyserRef.current.fftSize = configRef.current.fftSize;
        analyserRef.current.smoothingTimeConstant =
          configRef.current.smoothingTimeConstant;
        analyserRef.current.minDecibels = configRef.current.minDecibels;
        analyserRef.current.maxDecibels = configRef.current.maxDecibels;

        // Create source from stream
        sourceRef.current =
          audioContextRef.current.createMediaStreamSource(stream);
        sourceRef.current.connect(analyserRef.current);

        setIsAnalyzing(true);
        analyze();
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to start audio analysis";
        setError(errorMessage);
        throw err;
      }
    },
    [analyze],
  );

  // Stop analysis
  const stopAnalysis = useCallback(() => {
    setIsAnalyzing(false);

    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    if (sourceRef.current) {
      sourceRef.current.disconnect();
      sourceRef.current = null;
    }

    if (audioContextRef.current && audioContextRef.current.state !== "closed") {
      void void audioContextRef.current.close();
      audioContextRef.current = null;
    }

    analyserRef.current = null;
    setAnalysisData(null);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopAnalysis();
    };
  }, [stopAnalysis]);

  return {
    analysisData,
    isAnalyzing,
    error,
    startAnalysis,
    stopAnalysis,
    updateConfig,
  };
};
