/**
 * AudioWorkletProcessor downsampling microphone audio to 16kHz mono linear 16-bit PCM.
 *
 * Runs strictly on the Web Audio rendering thread to avoid main-thread UI jank.
 */

class PCMRecorderWorklet extends AudioWorkletProcessor {
  constructor() {
    super();
    this.targetSampleRate = 16000;
    // Buffer for 100ms frames at 16kHz (1600 samples)
    this.frameSize = 1600;
    this.buffer = new Int16Array(this.frameSize * 4);
    this.bufferIndex = 0;

    // Resampling state tracking
    this.resampleRatio = currentFrame ? 1 : 1;
    this.lastInputSample = 0.0;
    this.resamplePhase = 0.0;
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0];
    if (!input || input.length === 0) {
      return true;
    }

    const inputChannel = input[0];
    if (!inputChannel || inputChannel.length === 0) {
      return true;
    }

    const inputLength = inputChannel.length;
    const ratio = sampleRate / this.targetSampleRate;

    // Resample from current sampleRate (e.g. 48kHz / 44.1kHz) to 16kHz using linear interpolation
    while (this.resamplePhase < inputLength) {
      const index = Math.floor(this.resamplePhase);
      const frac = this.resamplePhase - index;

      const s0 = index > 0 ? inputChannel[index - 1] : this.lastInputSample;
      const s1 = inputChannel[index];
      const interpolated = s0 + frac * (s1 - s0);

      // Quantize Float32 [-1.0, 1.0] to signed 16-bit linear PCM [-32768, 32767]
      const clamped = Math.max(-1.0, Math.min(1.0, interpolated));
      const pcmSample = clamped < 0 ? Math.round(clamped * 32768) : Math.round(clamped * 32767);

      this.buffer[this.bufferIndex++] = pcmSample;

      // When we accumulate 100ms of audio (1600 samples at 16kHz)
      if (this.bufferIndex >= this.frameSize) {
        const chunk = this.buffer.slice(0, this.frameSize);
        // Transfer ArrayBuffer to main thread with zero-copy
        this.port.postMessage(
          {
            event: "chunk",
            buffer: chunk.buffer,
            sampleRate: this.targetSampleRate,
            samples: this.frameSize,
          },
          [chunk.buffer]
        );
        this.bufferIndex = 0;
      }

      this.resamplePhase += ratio;
    }

    this.resamplePhase -= inputLength;
    this.lastInputSample = inputChannel[inputLength - 1];

    return true;
  }
}

registerProcessor("pcm-recorder-worklet", PCMRecorderWorklet);
