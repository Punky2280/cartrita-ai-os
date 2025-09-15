// Cartrita AI OS - Waveform Visualizer Component Tests
// Comprehensive tests for real-time waveform rendering

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import WaveformVisualizer from "../WaveformVisualizer";
import { AudioAnalysisData } from "../../hooks/useAudioAnalysis";

// Mock canvas
const mockCanvas = {
  getContext: vi.fn(() => mockCanvasContext),
  width: 400,
  height: 200,
  style: {},
};

const mockCanvasContext = {
  canvas: mockCanvas,
  beginPath: vi.fn(),
  stroke: vi.fn(),
  moveTo: vi.fn(),
  lineTo: vi.fn(),
  fillRect: vi.fn(),
  fill: vi.fn(),
  createLinearGradient: vi.fn(() => ({
    addColorStop: vi.fn(),
  })),
  scale: vi.fn(),
  fillStyle: "",
  strokeStyle: "",
  lineWidth: 1,
  lineCap: "butt",
  lineJoin: "miter",
};

beforeAll(() => {
  // Mock HTMLCanvasElement
  Object.defineProperty(HTMLCanvasElement.prototype, "getContext", {
    value: vi.fn(() => mockCanvasContext),
    writable: true,
  });

  // Mock window.devicePixelRatio
  Object.defineProperty(window, "devicePixelRatio", {
    value: 2,
    writable: true,
  });
});

describe("WaveformVisualizer", () => {
  const mockAnalysisData: AudioAnalysisData = {
    frequencyData: new Uint8Array([100, 150, 200, 180, 120]),
    timeData: new Uint8Array([128, 160, 200, 180, 100]),
    volume: 0.7,
    dominantFrequency: 440,
    isActive: true,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("Rendering", () => {
    it("should render canvas element", () => {
      render(<WaveformVisualizer analysisData={mockAnalysisData} />);

      const canvas = screen.getByLabelText("Audio waveform visualization");
      expect(canvas).toBeInTheDocument();
      expect(canvas.tagName).toBe("CANVAS");
    });

    it("should apply custom dimensions", () => {
      render(
        <WaveformVisualizer
          analysisData={mockAnalysisData}
          width={800}
          height={400}
        />,
      );

      const canvas = screen.getByLabelText("Audio waveform visualization");
      expect(canvas).toHaveStyle({ width: "800px", height: "400px" });
    });

    it("should apply custom className and style", () => {
      const customStyle = { border: "1px solid red" };

      render(
        <WaveformVisualizer
          analysisData={mockAnalysisData}
          className="custom-waveform"
          style={customStyle}
        />,
      );

      const container = screen.getByLabelText(
        "Audio waveform visualization",
      ).parentElement;
      expect(container).toHaveClass("custom-waveform");
      expect(container).toHaveStyle(customStyle);
    });
  });

  describe("Waveform Drawing", () => {
    it("should draw waveform when data is provided", () => {
      render(<WaveformVisualizer analysisData={mockAnalysisData} />);

      // Canvas context methods should be called
      expect(mockCanvasContext.beginPath).toHaveBeenCalled();
      expect(mockCanvasContext.stroke).toHaveBeenCalled();
    });

    it("should not draw when no data is provided", () => {
      render(<WaveformVisualizer analysisData={null} />);

      expect(mockCanvasContext.beginPath).not.toHaveBeenCalled();
      expect(mockCanvasContext.stroke).not.toHaveBeenCalled();
    });

    it("should apply custom color", () => {
      render(
        <WaveformVisualizer
          analysisData={mockAnalysisData}
          color="#ff0000"
          gradient={false}
        />,
      );

      expect(mockCanvasContext.strokeStyle).toBe("#ff0000");
    });

    it("should apply custom line width", () => {
      render(
        <WaveformVisualizer analysisData={mockAnalysisData} lineWidth={4} />,
      );

      expect(mockCanvasContext.lineWidth).toBe(4);
    });
  });

  describe("Frequency Bars Mode", () => {
    it("should draw frequency bars when enabled", () => {
      render(
        <WaveformVisualizer
          analysisData={mockAnalysisData}
          showFrequencyBars={true}
        />,
      );

      expect(mockCanvasContext.fillRect).toHaveBeenCalled();
    });

    it("should draw waveform when frequency bars disabled", () => {
      render(
        <WaveformVisualizer
          analysisData={mockAnalysisData}
          showFrequencyBars={false}
        />,
      );

      expect(mockCanvasContext.beginPath).toHaveBeenCalled();
      expect(mockCanvasContext.stroke).toHaveBeenCalled();
    });
  });

  describe("Gradient Rendering", () => {
    it("should create gradient when enabled", () => {
      render(
        <WaveformVisualizer analysisData={mockAnalysisData} gradient={true} />,
      );

      expect(mockCanvasContext.createLinearGradient).toHaveBeenCalled();
    });

    it("should not create gradient when disabled", () => {
      render(
        <WaveformVisualizer analysisData={mockAnalysisData} gradient={false} />,
      );

      expect(mockCanvasContext.createLinearGradient).not.toHaveBeenCalled();
    });
  });

  describe("Smoothing", () => {
    it("should apply smoothing when enabled", () => {
      render(
        <WaveformVisualizer analysisData={mockAnalysisData} smoothing={true} />,
      );

      // With smoothing, lineTo should be called for each data point
      expect(mockCanvasContext.lineTo).toHaveBeenCalled();
    });

    it("should not apply smoothing when disabled", () => {
      render(
        <WaveformVisualizer
          analysisData={mockAnalysisData}
          smoothing={false}
        />,
      );

      // Without smoothing, should still call lineTo but differently
      expect(mockCanvasContext.lineTo).toHaveBeenCalled();
    });
  });

  describe("Performance Monitoring", () => {
    it("should show FPS in development mode", () => {
      const originalEnv = process.env.NODE_ENV;
      vi.stubEnv("NODE_ENV", "development");

      render(<WaveformVisualizer analysisData={mockAnalysisData} />);

      const fpsElement = screen.getByText(/FPS/);
      expect(fpsElement).toBeInTheDocument();

      // Restore using delete then reassign pattern to satisfy readonly typing
      const orig = originalEnv;
      delete (process.env as Record<string, string>)["NODE_ENV"];
      if (orig !== undefined) {
        (process.env as Record<string, string>)["NODE_ENV"] = orig;
      }
    });

    it("should not show FPS in production mode", () => {
      const originalEnv = process.env.NODE_ENV;
      vi.stubEnv("NODE_ENV", "production");

      render(<WaveformVisualizer analysisData={mockAnalysisData} />);

      const fpsElement = screen.queryByText(/FPS/);
      expect(fpsElement).not.toBeInTheDocument();

      const orig2 = originalEnv;
      delete (process.env as Record<string, string>)["NODE_ENV"];
      if (orig2 !== undefined) {
        (process.env as Record<string, string>)["NODE_ENV"] = orig2;
      }
    });
  });

  describe("Canvas Setup", () => {
    it("should set up canvas with device pixel ratio", () => {
      render(<WaveformVisualizer analysisData={mockAnalysisData} />);

      expect(mockCanvasContext.scale).toHaveBeenCalledWith(2, 2);
    });

    it("should handle canvas resize", () => {
      const { rerender } = render(
        <WaveformVisualizer
          analysisData={mockAnalysisData}
          width={400}
          height={200}
        />,
      );

      rerender(
        <WaveformVisualizer
          analysisData={mockAnalysisData}
          width={800}
          height={400}
        />,
      );

      // Canvas should be resized
      expect(mockCanvasContext.scale).toHaveBeenCalled();
    });
  });

  describe("Accessibility", () => {
    it("should have proper aria-label", () => {
      render(<WaveformVisualizer analysisData={mockAnalysisData} />);

      const canvas = screen.getByLabelText("Audio waveform visualization");
      expect(canvas).toBeInTheDocument();
    });
  });
});
