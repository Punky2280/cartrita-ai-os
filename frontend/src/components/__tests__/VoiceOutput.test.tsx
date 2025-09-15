// Cartrita AI OS - VoiceOutput Component Tests
// Unit tests for voice output functionality

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import { VoiceOutput } from "@/components/VoiceOutput";
import { useVoice } from "@/hooks";

// Mock AudioContext for tests
class MockAudioContext {
  createGain() {
    return {
      connect: vi.fn(),
      gain: {
        setValueAtTime: vi.fn(),
      },
    };
  }
  close() {
    return Promise.resolve();
  }
  currentTime = 0;
}

// Mock window.AudioContext
Object.defineProperty(window, "AudioContext", {
  writable: true,
  value: MockAudioContext,
});

// Mock the useVoice hook
vi.mock("@/hooks", () => ({
  useVoice: vi.fn(),
}));

const mockUseVoice = useVoice as any;

describe("VoiceOutput", () => {
  beforeEach(() => {
    mockUseVoice.mockReturnValue({
      speak: vi.fn(),
      isSpeaking: false,
      voiceState: "idle",
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("renders voice output controls", () => {
    render(<VoiceOutput />);

    expect(screen.getByText("Voice Output")).toBeInTheDocument();
    expect(screen.getByText("Test Voice")).toBeInTheDocument();
    expect(screen.getByText("Volume")).toBeInTheDocument();
    expect(screen.getByText("Speed")).toBeInTheDocument();
  });

  it("displays voice selection dropdown", () => {
    render(<VoiceOutput />);

    // Look for the select trigger button specifically
    const selectTrigger = screen.getByRole("button", { name: "Voice" });
    expect(selectTrigger).toBeInTheDocument();
  });

  it("calls speak function when test voice button is clicked", async () => {
    const mockSpeak = vi.fn();
    mockUseVoice.mockReturnValue({
      speak: mockSpeak,
      isSpeaking: false,
      voiceState: "idle",
    });

    render(<VoiceOutput />);

    const testButton = screen.getByText("Test Voice");
    fireEvent.click(testButton);

    await waitFor(() => {
      expect(mockSpeak).toHaveBeenCalledWith(
        "Hello! This is a test of the voice output system.",
      );
    });
  });

  it("shows speaking state when voice is active", () => {
    mockUseVoice.mockReturnValue({
      speak: vi.fn(),
      isSpeaking: true,
      voiceState: "speaking",
    });

    render(<VoiceOutput />);

    expect(screen.getByText("Speaking...")).toBeInTheDocument();
  });

  it("disables test button when speaking", () => {
    mockUseVoice.mockReturnValue({
      speak: vi.fn(),
      isSpeaking: true,
      voiceState: "speaking",
    });

    render(<VoiceOutput />);

    const testButton = screen.getByRole("button", { name: /speaking/i });
    expect(testButton).toBeDisabled();
  });
});
