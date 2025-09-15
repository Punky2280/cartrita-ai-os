// Cartrita AI OS - Voice Output Component
// Advanced TTS with voice selection and playback controls

import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import {
  Volume2,
  VolumeX,
  Play,
  Pause,
  Square,
  RotateCcw,
  Settings,
  CheckCircle,
  AlertCircle,
  Loader2,
  ChevronDown,
  User,
} from "lucide-react";
import { cn } from "@/utils";
import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Slider,
  Badge,
  Alert,
  AlertDescription,
} from "@/components/ui";
import { useVoice } from "@/hooks";
import type { VoiceSettings } from "@/types";

// Voice options for Deepgram TTS
const VOICE_OPTIONS = [
  {
    id: "aura-asteria-en",
    name: "Asteria",
    gender: "female",
    accent: "American",
  },
  { id: "aura-luna-en", name: "Luna", gender: "female", accent: "American" },
  {
    id: "aura-stella-en",
    name: "Stella",
    gender: "female",
    accent: "American",
  },
  {
    id: "aura-athena-en",
    name: "Athena",
    gender: "female",
    accent: "American",
  },
  { id: "aura-hera-en", name: "Hera", gender: "female", accent: "American" },
  { id: "aura-orion-en", name: "Orion", gender: "male", accent: "American" },
  { id: "aura-arcas-en", name: "Arcas", gender: "male", accent: "American" },
  {
    id: "aura-perseus-en",
    name: "Perseus",
    gender: "male",
    accent: "American",
  },
  { id: "aura-angus-en", name: "Angus", gender: "male", accent: "British" },
  {
    id: "aura-orpheus-en",
    name: "Orpheus",
    gender: "male",
    accent: "American",
  },
];

export interface VoiceOutputProps {
  className?: string;
  onVoiceStart?: () => void;
  onVoiceEnd?: () => void;
  onError?: (error: Error) => void;
}

export function VoiceOutput({
  className,
  onVoiceStart,
  onVoiceEnd,
  onError,
}: VoiceOutputProps) {
  // Voice state management
  const { speak, isSpeaking, voiceState } = useVoice();

  // Component state
  const [selectedVoice, setSelectedVoice] = useState("aura-asteria-en");
  const [volume, setVolume] = useState(80);
  const [speed, setSpeed] = useState(1.0);
  const [isMuted, setIsMuted] = useState(false);
  const [currentText, setCurrentText] = useState("");
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackProgress, setPlaybackProgress] = useState(0);

  // Refs
  const audioContextRef = useRef<AudioContext | null>(null);
  const gainNodeRef = useRef<GainNode | null>(null);
  const playbackTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize audio context
  useEffect(() => {
    try {
      // Check if AudioContext is available (not in test environment)
      if (
        typeof AudioContext !== "undefined" ||
        typeof (window as any).webkitAudioContext !== "undefined"
      ) {
        audioContextRef.current = new (AudioContext ||
          (window as any).webkitAudioContext)();
        gainNodeRef.current = audioContextRef.current.createGain();
        gainNodeRef.current.connect(audioContextRef.current.destination);
      }
    } catch (error) {
      console.error("Failed to initialize audio context:", error);
      onError?.(error as Error);
    }

    return () => {
      if (
        audioContextRef.current &&
        typeof audioContextRef.current.close === "function"
      ) {
        void void audioContextRef.current.close();
      }
      if (playbackTimeoutRef.current) {
        clearTimeout(playbackTimeoutRef.current);
      }
    };
  }, [onError]);

  // Update volume
  useEffect(() => {
    if (gainNodeRef.current) {
      const actualVolume = isMuted ? 0 : volume / 100;
      gainNodeRef.current.gain.setValueAtTime(
        actualVolume,
        audioContextRef.current?.currentTime || 0,
      );
    }
  }, [volume, isMuted]);

  // Handle voice playback
  const handleSpeak = useCallback(
    async (text: string) => {
      if (!text.trim()) {
        toast.error("Please enter text to speak");
        return;
      }

      try {
        setIsPlaying(true);
        setCurrentText(text);
        setPlaybackProgress(0);
        onVoiceStart?.();

        // Use the existing voice hook's speak function
        await speak(text);

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
            setIsPlaying(false);
            setPlaybackProgress(100);
            onVoiceEnd?.();
          }
        }, interval);

        playbackTimeoutRef.current = setTimeout(() => {
          clearInterval(progressInterval);
          setIsPlaying(false);
          setPlaybackProgress(100);
          onVoiceEnd?.();
        }, duration);
      } catch (error) {
        console.error("Voice playback error:", error);
        setIsPlaying(false);
        setPlaybackProgress(0);
        onError?.(error as Error);
        toast.error("Failed to play voice");
      }
    },
    [speak, onVoiceStart, onVoiceEnd, onError],
  );

  // Stop playback
  const handleStop = useCallback(() => {
    if (playbackTimeoutRef.current) {
      clearTimeout(playbackTimeoutRef.current);
    }
    setIsPlaying(false);
    setPlaybackProgress(0);
    onVoiceEnd?.();
  }, [onVoiceEnd]);

  // Toggle mute
  const handleToggleMute = useCallback(() => {
    setIsMuted(!isMuted);
  }, [isMuted]);

  // Keyboard navigation
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      // Space or Enter to test voice
      if (
        (event.key === " " || event.key === "Enter") &&
        !isPlaying &&
        !isSpeaking
      ) {
        event.preventDefault();
        handleSpeak("Hello! This is a test of the voice output system.");
      }

      // Escape to stop playback
      if (event.key === "Escape" && isPlaying) {
        event.preventDefault();
        handleStop();
      }

      // M key to toggle mute
      if (event.key === "m" || event.key === "M") {
        event.preventDefault();
        handleToggleMute();
      }
    },
    [isPlaying, isSpeaking, handleSpeak, handleStop, handleToggleMute],
  );

  // Add keyboard event listener
  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  // Get current voice info
  const currentVoice = VOICE_OPTIONS.find((v) => v.id === selectedVoice);

  return (
    <Card className={cn("w-full max-w-md", className)}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Volume2 className="h-5 w-5" />
          Voice Output
          {isSpeaking && (
            <motion.div
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 1, repeat: Infinity }}
            >
              <div className="h-2 w-2 bg-green-500 rounded-full" />
            </motion.div>
          )}
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Voice Selection */}
        <div className="space-y-2">
          <label
            htmlFor="voice-select"
            className="text-sm font-medium"
            id="voice-select-label"
          >
            Voice
          </label>
          <Select value={selectedVoice} onValueChange={setSelectedVoice}>
            <SelectTrigger
              id="voice-select"
              aria-labelledby="voice-select-label"
              aria-describedby="voice-select-description"
            >
              <SelectValue>
                <div className="flex items-center gap-2">
                  <User className="h-4 w-4" aria-hidden="true" />
                  {currentVoice?.name || "Select Voice"}
                  {currentVoice && (
                    <Badge
                      variant="secondary"
                      className="text-xs"
                      aria-label={`Gender: ${currentVoice.gender}, Accent: ${currentVoice.accent}`}
                    >
                      {currentVoice.gender} • {currentVoice.accent}
                    </Badge>
                  )}
                </div>
              </SelectValue>
            </SelectTrigger>
            <SelectContent>
              {VOICE_OPTIONS.map((voice) => (
                <SelectItem
                  key={voice.id}
                  value={voice.id}
                  aria-label={`${voice.name} - ${voice.gender} voice with ${voice.accent} accent`}
                >
                  <div className="flex items-center gap-2">
                    <User className="h-4 w-4" aria-hidden="true" />
                    {voice.name}
                    <Badge variant="outline" className="text-xs">
                      {voice.gender} • {voice.accent}
                    </Badge>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <div id="voice-select-description" className="sr-only">
            Select a voice for text-to-speech output
          </div>
        </div>

        {/* Volume Control */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label
              htmlFor="volume-slider"
              className="text-sm font-medium"
              id="volume-label"
            >
              Volume
            </label>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleToggleMute}
              className="h-8 w-8 p-0"
              aria-label={isMuted ? "Unmute volume" : "Mute volume"}
              aria-pressed={isMuted}
            >
              {isMuted ? (
                <VolumeX className="h-4 w-4" aria-hidden="true" />
              ) : (
                <Volume2 className="h-4 w-4" aria-hidden="true" />
              )}
            </Button>
          </div>
          <Slider
            value={[volume]}
            onValueChange={(value) => setVolume(value[0])}
            max={100}
            min={0}
            step={1}
            className="w-full"
            disabled={isMuted}
            id="volume-slider"
            aria-labelledby="volume-label"
            aria-describedby="volume-value"
            aria-valuetext={`${volume}% volume`}
          />
          <div
            id="volume-value"
            className="text-xs text-muted-foreground text-center"
            aria-live="polite"
          >
            {isMuted ? "Muted" : `${volume}%`}
          </div>
        </div>

        {/* Speed Control */}
        <div className="space-y-2">
          <label
            htmlFor="speed-slider"
            className="text-sm font-medium"
            id="speed-label"
          >
            Speed
          </label>
          <Slider
            value={[speed]}
            onValueChange={(value) => setSpeed(value[0])}
            max={2.0}
            min={0.5}
            step={0.1}
            className="w-full"
            id="speed-slider"
            aria-labelledby="speed-label"
            aria-describedby="speed-value"
            aria-valuetext={`${speed.toFixed(1)} times speed`}
          />
          <div
            id="speed-value"
            className="text-xs text-muted-foreground text-center"
            aria-live="polite"
          >
            {speed.toFixed(1)}x
          </div>
        </div>

        {/* Playback Progress */}
        <AnimatePresence>
          {isPlaying && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="space-y-2"
            >
              <div className="flex items-center gap-2">
                <div className="flex-1 bg-secondary rounded-full h-2">
                  <motion.div
                    className="bg-primary h-2 rounded-full"
                    style={{ width: `${playbackProgress}%` }}
                    transition={{ duration: 0.1 }}
                  />
                </div>
                <span className="text-xs text-muted-foreground">
                  {Math.round(playbackProgress)}%
                </span>
              </div>
              {currentText && (
                <div className="text-xs text-muted-foreground bg-muted p-2 rounded">
                  {currentText.length > 100
                    ? `${currentText.substring(0, 100)}...`
                    : currentText}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Status Messages */}
        <AnimatePresence>
          {voiceState === "error" && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
            >
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Voice playback failed. Please try again.
                </AlertDescription>
              </Alert>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Control Buttons */}
        <div className="flex items-center gap-2 pt-2">
          <Button
            onClick={() => {
              {
                handleSpeak(
                  "Hello! This is a test of the voice output system.",
                );
              }
            }}
            disabled={isPlaying || isSpeaking}
            className="flex-1"
            aria-describedby="test-voice-description"
          >
            {isPlaying || isSpeaking ? (
              <>
                <Loader2
                  className="h-4 w-4 mr-2 animate-spin"
                  aria-hidden="true"
                />
                Speaking...
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" aria-hidden="true" />
                Test Voice
              </>
            )}
          </Button>

          {isPlaying && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleStop}
              aria-label="Stop voice playback"
            >
              <Square className="h-4 w-4" aria-hidden="true" />
            </Button>
          )}
        </div>
        <div id="test-voice-description" className="sr-only">
          Test the selected voice with a sample message
        </div>

        {/* Status Indicator */}
        <div
          className="flex items-center justify-center gap-2 pt-2 border-t"
          role="status"
          aria-live="polite"
        >
          <div
            className={cn(
              "h-2 w-2 rounded-full",
              voiceState === "idle" && "bg-gray-400",
              voiceState === "speaking" && "bg-green-500",
              voiceState === "error" && "bg-red-500",
            )}
            aria-hidden="true"
          />
          <span
            className="text-xs text-muted-foreground capitalize"
            aria-label={`Voice status: ${voiceState}`}
          >
            {voiceState}
          </span>
        </div>

        {/* Keyboard Shortcuts */}
        <details className="mt-4">
          <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">
            Keyboard Shortcuts
          </summary>
          <div className="mt-2 text-xs text-muted-foreground space-y-1">
            <div>
              <kbd className="px-1 py-0.5 bg-muted rounded text-xs">Space</kbd>{" "}
              or{" "}
              <kbd className="px-1 py-0.5 bg-muted rounded text-xs">Enter</kbd>{" "}
              - Test voice
            </div>
            <div>
              <kbd className="px-1 py-0.5 bg-muted rounded text-xs">Esc</kbd> -
              Stop playback
            </div>
            <div>
              <kbd className="px-1 py-0.5 bg-muted rounded text-xs">M</kbd> -
              Toggle mute
            </div>
          </div>
        </details>
      </CardContent>
    </Card>
  );
}

export default VoiceOutput;
