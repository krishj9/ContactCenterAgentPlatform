/**
 * Real-time audio waveform visualizer using Web Audio API AnalyserNode and Canvas.
 *
 * Renders smooth animated audio waves during live speech and an elegant idle pulse wave when silent.
 */

import { useRef, useEffect } from "react";

export interface WaveformVisualizerProps {
  analyserNode: AnalyserNode | null;
  isActive: boolean;
  audioLevel?: number;
  className?: string;
  height?: number;
}

export function WaveformVisualizer({
  analyserNode,
  isActive,
  audioLevel = 0,
  className = "",
  height = 80,
}: WaveformVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const phaseRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Handle high DPI displays
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);

    const bufferLength = analyserNode ? analyserNode.frequencyBinCount : 128;
    const timeDomainData = new Uint8Array(bufferLength);

    const render = () => {
      const width = rect.width;
      const h = height;

      ctx.clearRect(0, 0, width, h);

      if (isActive && analyserNode) {
        analyserNode.getByteTimeDomainData(timeDomainData);

        // Gradient wave line
        const gradient = ctx.createLinearGradient(0, 0, width, 0);
        gradient.addColorStop(0, "rgba(59, 130, 246, 0.4)");
        gradient.addColorStop(0.3, "rgba(16, 185, 129, 0.9)");
        gradient.addColorStop(0.7, "rgba(99, 102, 241, 0.9)");
        gradient.addColorStop(1, "rgba(59, 130, 246, 0.4)");

        ctx.lineWidth = 2.5;
        ctx.strokeStyle = gradient;
        ctx.shadowColor = "rgba(59, 130, 246, 0.5)";
        ctx.shadowBlur = 8;
        ctx.beginPath();

        const sliceWidth = width / bufferLength;
        let x = 0;

        for (let i = 0; i < bufferLength; i++) {
          const v = timeDomainData[i] / 128.0;
          // Scale amplitude
          const y = (v * h) / 2;

          if (i === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }

          x += sliceWidth;
        }

        ctx.lineTo(width, h / 2);
        ctx.stroke();

        // Second subtle secondary wave
        ctx.beginPath();
        ctx.lineWidth = 1.0;
        ctx.strokeStyle = "rgba(147, 197, 253, 0.35)";
        ctx.shadowBlur = 0;
        x = 0;
        phaseRef.current += 0.05;

        for (let i = 0; i < bufferLength; i++) {
          const v = timeDomainData[i] / 128.0;
          const offset = Math.sin(i * 0.1 + phaseRef.current) * (audioLevel * 10);
          const y = (v * h) / 2 + offset;

          if (i === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
          x += sliceWidth;
        }
        ctx.stroke();
      } else {
        // Idle gentle breathing sine wave
        phaseRef.current += 0.03;
        const centerY = h / 2;

        ctx.beginPath();
        ctx.lineWidth = 1.5;
        ctx.strokeStyle = "rgba(100, 116, 139, 0.4)";
        ctx.shadowColor = "rgba(59, 130, 246, 0.2)";
        ctx.shadowBlur = 4;

        for (let x = 0; x <= width; x += 4) {
          const wavelength = 0.015;
          const amp = 3 + Math.sin(phaseRef.current * 0.5) * 2;
          const y = centerY + Math.sin(x * wavelength + phaseRef.current) * amp;

          if (x === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        }
        ctx.stroke();
      }

      animFrameRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
      }
    };
  }, [analyserNode, isActive, audioLevel, height]);

  return (
    <div className={`relative w-full rounded-xl overflow-hidden bg-slate-950/70 border border-slate-800/80 p-2 flex flex-col justify-center ${className}`}>
      <canvas
        ref={canvasRef}
        style={{ width: "100%", height: `${height}px` }}
        className="block"
      />
      {/* Audio Level Meter Overlay */}
      <div className="absolute right-3 top-2 flex items-center gap-1.5 text-[10px] font-mono text-slate-400">
        <span className={`h-1.5 w-1.5 rounded-full ${isActive ? "bg-emerald-400 animate-pulse" : "bg-slate-600"}`} />
        <span>{isActive ? `${Math.round(audioLevel * 100)}% MIC` : "MIC OFF"}</span>
      </div>
    </div>
  );
}
