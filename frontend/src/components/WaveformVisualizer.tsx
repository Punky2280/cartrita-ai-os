// Cartrita AI OS - Waveform Visualizer Component
// Real-time audio waveform visualization with Canvas/WebGL rendering

import React, { useRef, useEffect, useCallback, useState } from "react";
import { AudioAnalysisData } from "../hooks/useAudioAnalysis";

export interface WaveformVisualizerProps {
  analysisData: AudioAnalysisData | null;
  width?: number;
  height?: number;
  className?: string;
  style?: React.CSSProperties;
  color?: string;
  backgroundColor?: string;
  lineWidth?: number;
  showFrequencyBars?: boolean;
  smoothing?: boolean;
  gradient?: boolean;
}

export interface WaveformVisualizerRef {
  canvas: HTMLCanvasElement | null;
}

const WaveformVisualizer: React.ForwardRefRenderFunction<
  WaveformVisualizerRef,
  WaveformVisualizerProps
> = (
  {
    analysisData,
    width = 400,
    height = 200,
    className = "",
    style = {},
    color = "#3b82f6",
    backgroundColor = "#1f2937",
    lineWidth = 2,
    showFrequencyBars = false,
    smoothing = true,
    gradient = true,
  },
  ref,
) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number | null>(null);
  const [fps, setFps] = useState(0);

  // FPS monitoring for performance tracking
  const fpsRef = useRef({ frames: 0, lastTime: Date.now() });

  // Expose canvas ref
  React.useImperativeHandle(
    ref,
    () => ({
      canvas: canvasRef.current,
    }),
    [],
  );

  // Draw waveform
  const drawWaveform = useCallback(
    (ctx: CanvasRenderingContext2D, data: Uint8Array) => {
      const { width: canvasWidth, height: canvasHeight } = ctx.canvas;
      const centerY = canvasHeight / 2;
      const sliceWidth = canvasWidth / data.length;

      ctx.beginPath();
      ctx.strokeStyle = color;
      ctx.lineWidth = lineWidth;
      ctx.lineCap = "round";
      ctx.lineJoin = "round";

      if (gradient) {
        const gradient = ctx.createLinearGradient(0, 0, canvasWidth, 0);
        gradient.addColorStop(0, color);
        gradient.addColorStop(0.5, "#60a5fa");
        gradient.addColorStop(1, color);
        ctx.strokeStyle = gradient;
      }

      let x = 0;
      for (let i = 0; i < data.length; i++) {
        const amplitude = (data[i] - 128) / 128; // Normalize to -1 to 1
        const y = centerY + amplitude * centerY * 0.8;

        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          if (smoothing) {
            ctx.lineTo(x, y);
          } else {
            ctx.lineTo(
              x,
              centerY + ((data[i - 1] - 128) / 128) * centerY * 0.8,
            );
            ctx.lineTo(x, y);
          }
        }

        x += sliceWidth;
      }

      ctx.stroke();
    },
    [color, lineWidth, gradient, smoothing],
  );

  // Draw frequency bars
  const drawFrequencyBars = useCallback(
    (ctx: CanvasRenderingContext2D, data: Uint8Array) => {
      const { width: canvasWidth, height: canvasHeight } = ctx.canvas;
      const barWidth = canvasWidth / data.length;
      const barSpacing = 1;

      ctx.fillStyle = color;

      for (let i = 0; i < data.length; i++) {
        const barHeight = (data[i] / 255) * canvasHeight;
        const x = i * (barWidth + barSpacing);
        const y = canvasHeight - barHeight;

        if (gradient) {
          const gradient = ctx.createLinearGradient(0, canvasHeight, 0, y);
          gradient.addColorStop(0, color);
          gradient.addColorStop(1, "#60a5fa");
          ctx.fillStyle = gradient;
        }

        ctx.fillRect(x, y, barWidth, barHeight);
      }
    },
    [color, gradient],
  );

  // Main render function
  const render = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !analysisData) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Clear canvas
    ctx.fillStyle = backgroundColor;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw based on mode
    if (showFrequencyBars) {
      drawFrequencyBars(ctx, analysisData.frequencyData);
    } else {
      drawWaveform(ctx, analysisData.timeData);
    }

    // FPS calculation
    fpsRef.current.frames++;
    const now = Date.now();
    if (now - fpsRef.current.lastTime >= 1000) {
      setFps(fpsRef.current.frames);
      fpsRef.current.frames = 0;
      fpsRef.current.lastTime = now;
    }

    // Continue animation if active
    if (analysisData.isActive) {
      animationFrameRef.current = requestAnimationFrame(render);
    }
  }, [
    analysisData,
    backgroundColor,
    showFrequencyBars,
    drawWaveform,
    drawFrequencyBars,
  ]);

  // Effect for rendering
  useEffect(() => {
    if (analysisData?.isActive) {
      render();
    } else if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [analysisData, render]);

  // Canvas setup
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // Set canvas size with device pixel ratio for crisp rendering
    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    const ctx = canvas.getContext("2d");
    if (ctx) {
      ctx.scale(dpr, dpr);
    }
  }, [width, height]);

  return (
    <div className={`waveform-visualizer ${className}`} style={style}>
      <canvas
        ref={canvasRef}
        className="waveform-canvas"
        style={{
          display: "block",
          backgroundColor,
          borderRadius: "4px",
        }}
        aria-label="Audio waveform visualization"
      />
      {process.env.NODE_ENV === "development" && (
        <div
          className="waveform-fps"
          style={{
            position: "absolute",
            top: "4px",
            right: "4px",
            fontSize: "12px",
            color: "#9ca3af",
            backgroundColor: "rgba(0, 0, 0, 0.5)",
            padding: "2px 4px",
            borderRadius: "2px",
            pointerEvents: "none",
          }}
        >
          {fps} FPS
        </div>
      )}
    </div>
  );
};

export default React.forwardRef(WaveformVisualizer);
