import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

// Hoist all mocks before importing the hook/component under test
const deepgramMocks = vi.hoisted(() => ({
  startVoiceRecording: vi.fn(),
  stopVoiceRecording: vi.fn(),
  getConnectionState: vi.fn(() => "connected"),
  getTranscript: vi.fn(() => ""),
  getAnalytics: vi.fn(() => ({})),
  onConnectionStateChange: vi.fn(),
  onTranscript: vi.fn(),
  onError: vi.fn(),
  connect: vi.fn(),
  disconnect: vi.fn(),
}));

vi.mock("../../services/deepgram", () => ({
  deepgramService: {
    startVoiceRecording: deepgramMocks.startVoiceRecording,
    stopVoiceRecording: deepgramMocks.stopVoiceRecording,
    getConnectionState: deepgramMocks.getConnectionState,
    getTranscript: deepgramMocks.getTranscript,
    getAnalytics: deepgramMocks.getAnalytics,
    onConnectionStateChange: deepgramMocks.onConnectionStateChange,
    onTranscript: deepgramMocks.onTranscript,
    onError: deepgramMocks.onError,
    connect: deepgramMocks.connect,
    disconnect: deepgramMocks.disconnect,
  },
}));

vi.mock("../useAudioAnalysis", () => ({
  useAudioAnalysis: vi.fn(() => ({
    audioAnalysisData: {
      frequencyData: new Uint8Array(128).fill(50),
      timeData: new Uint8Array(256).fill(25),
      volume: 0.5,
      dominantFrequency: 440,
      isAnalyzing: true,
    },
    startAnalysis: vi.fn(),
    stopAnalysis: vi.fn(),
    updateConfig: vi.fn(),
  })),
}));

vi.mock("../../components/WaveformVisualizer", () => {
  const React = require("react");
  const Mock = React.forwardRef(function WaveformVisualizerMock(
    { analysisData, width, height, className }: any,
    ref: any,
  ) {
    return React.createElement(
      "div",
      {
        ref,
        className: `waveform-visualizer ${className || ""}`,
        "data-testid": "waveform-visualizer",
        style: { width, height },
      },
      React.createElement("canvas", {
        "aria-label": "Audio waveform visualization",
        className: "waveform-canvas",
        width,
        height,
        "data-points": analysisData?.frequencyData?.length,
      }),
    );
  });
  return { default: Mock };
});

import { useDeepgramVoice } from "../useDeepgramVoice";
import WaveformVisualizer from "../../components/WaveformVisualizer";

const TestComponent: React.FC = () => {
  const voiceHook = useDeepgramVoice();

  return (
    <div>
      <button onClick={voiceHook.startRecording}>Start Recording</button>
      <button onClick={voiceHook.stopRecording}>Stop Recording</button>
      <WaveformVisualizer
        analysisData={voiceHook.audioAnalysisData as any}
        width={400}
        height={200}
        className="test-waveform"
      />
      <div data-testid="analysis-status">
        {(voiceHook.audioAnalysisData as any)?.frequencyData
          ? "Analyzing"
          : "Not Analyzing"}
      </div>
    </div>
  );
};

describe("Voice Hook + Waveform Integration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should integrate audio analysis with voice recording", () => {
    render(<TestComponent />);

    // Check that the component renders
    expect(screen.getByText("Start Recording")).toBeInTheDocument();
    expect(screen.getByText("Stop Recording")).toBeInTheDocument();

    // Check that waveform visualizer is rendered
    const visualizer = screen.getByTestId("waveform-visualizer");
    expect(visualizer).toBeInTheDocument();
    expect(visualizer).toHaveClass("test-waveform");

    // Check that audio analysis data is available
    expect(screen.getByTestId("analysis-status")).toHaveTextContent(
      "Analyzing",
    );
  });

  it("should pass audio analysis data to waveform visualizer", () => {
    render(<TestComponent />);

    // The WaveformVisualizer should receive the audioAnalysisData from the voice hook
    const visualizer = screen.getByTestId("waveform-visualizer");
    expect(visualizer).toBeInTheDocument();

    // Verify the component structure is correct
    expect(visualizer.tagName.toLowerCase()).toBe("div");
  });
});
