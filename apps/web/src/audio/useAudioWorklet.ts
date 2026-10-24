/**
 * React hook managing Web Audio API AudioWorklet microphone capture.
 *
 * Captures browser microphone, resamples on audio thread to 16kHz mono linear 16-bit PCM,
 * provides an AnalyserNode for canvas waveform rendering, and streams 100ms frames.
 */

import { useState, useRef, useCallback, useEffect } from "react";

export interface UseAudioWorkletOptions {
  onAudioChunk?: (pcmBuffer: ArrayBuffer, sequence: number) => void;
  targetSampleRate?: number;
}

export interface UseAudioWorkletReturn {
  isRecording: boolean;
  audioLevel: number;
  analyserNode: AnalyserNode | null;
  packetsSent: number;
  error: string | null;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
}

export function useAudioWorklet({
  onAudioChunk,
}: UseAudioWorkletOptions = {}): UseAudioWorkletReturn {
  const [isRecording, setIsRecording] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0.0);
  const [packetsSent, setPacketsSent] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const workletNodeRef = useRef<AudioWorkletNode | null>(null);
  const analyserNodeRef = useRef<AnalyserNode | null>(null);
  const sequenceRef = useRef(0);
  const animFrameRef = useRef<number | null>(null);

  const stopRecording = useCallback(() => {
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = null;
    }

    if (workletNodeRef.current) {
      workletNodeRef.current.disconnect();
      workletNodeRef.current = null;
    }

    if (analyserNodeRef.current) {
      analyserNodeRef.current.disconnect();
      analyserNodeRef.current = null;
    }

    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((t) => t.stop());
      mediaStreamRef.current = null;
    }

    if (audioContextRef.current && audioContextRef.current.state !== "closed") {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }

    setIsRecording(false);
    setAudioLevel(0.0);
  }, []);

  const startRecording = useCallback(async () => {
    try {
      setError(null);
      sequenceRef.current = 0;
      setPacketsSent(0);

      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      mediaStreamRef.current = stream;

      // Initialize AudioContext
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const ctx = new AudioCtx();
      audioContextRef.current = ctx;

      if (ctx.state === "suspended") {
        await ctx.resume();
      }

      // Load PCM downsampler AudioWorklet
      await ctx.audioWorklet.addModule("/pcm-recorder-worklet.js");

      // Build Audio Node Graph
      const source = ctx.createMediaStreamSource(stream);

      // AnalyserNode for canvas visualizer
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.8;
      analyserNodeRef.current = analyser;

      // Worklet Node
      const workletNode = new AudioWorkletNode(ctx, "pcm-recorder-worklet");
      workletNodeRef.current = workletNode;

      // Mute gain node to prevent speaker feedback loop
      const muteGain = ctx.createGain();
      muteGain.gain.value = 0.0;

      // Connect: mic source -> analyser -> worklet -> mute -> destination
      source.connect(analyser);
      analyser.connect(workletNode);
      workletNode.connect(muteGain);
      muteGain.connect(ctx.destination);

      // Handle audio chunks emitted by worklet thread
      workletNode.port.onmessage = (event: MessageEvent) => {
        if (event.data?.event === "chunk" && event.data?.buffer) {
          const seq = sequenceRef.current++;
          setPacketsSent(seq + 1);
          onAudioChunk?.(event.data.buffer, seq);
        }
      };

      // Real-time audio level monitoring loop
      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const updateLevel = () => {
        if (!analyserNodeRef.current) return;
        analyserNodeRef.current.getByteFrequencyData(dataArray);

        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i];
        }
        const avg = sum / dataArray.length;
        setAudioLevel(Math.min(1.0, avg / 128.0));

        animFrameRef.current = requestAnimationFrame(updateLevel);
      };
      updateLevel();

      setIsRecording(true);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(`Microphone capture error: ${msg}`);
      stopRecording();
    }
  }, [onAudioChunk, stopRecording]);

  useEffect(() => {
    return () => {
      stopRecording();
    };
  }, [stopRecording]);

  return {
    isRecording,
    audioLevel,
    analyserNode: analyserNodeRef.current,
    packetsSent,
    error,
    startRecording,
    stopRecording,
  };
}
