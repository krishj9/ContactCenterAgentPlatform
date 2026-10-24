# ADR-002: Realtime Streaming Audio over AudioWorklet 16kHz PCM

* **Status**: Accepted
* **Date**: 2026-10-23
* **Deciders**: Architecture Review Board
* **Context**: Technical Specification §2.2, Requirements R6/R7

---

## Context & Problem Statement
The Customer View (`/customer`) and Agent Cockpit require real-time streaming audio capture from browser microphones with minimal latency, low bandwidth overhead, and zero reliance on heavy third-party telephony plugins or proprietary WebRTC media gateways.

Standard browser `MediaRecorder` generates WebM/Opus blobs chunked at 1-second intervals, introducing buffer latency and requiring server-side transcoding before ingestion by speech-to-text models like Cloud STT or Whisper.

## Decision
We implemented client-side audio capture using the **Web Audio API + AudioWorklet** (`pcm-recorder-worklet.js`):
1. **Direct Worklet Processing**: An isolated audio thread runs off the browser main UI thread, capturing raw `Float32Array` samples.
2. **Client-Side Downsampling**: Automatically downsamples native hardware rates (44.1kHz or 48kHz) to standardized **16kHz mono 16-bit linear PCM**.
3. **Chunked Streaming**: Emits 100ms PCM byte frames directly over the active bidirectional WebSocket connection.

## Consequences

### Positive
* **Zero Buffer Lag**: Speech frames arrive at the backend gateway within ~100ms of utterance.
* **Direct STT Ingestion**: 16kHz mono linear PCM is natively consumed by Google Cloud Speech-to-Text V2 and local Faster-Whisper without server transcoding overhead.
* **Main Thread Performance**: AudioWorklet executes in a dedicated audio rendering context, ensuring 60fps UI rendering and zero audio crackling during React state updates.

### Negative / Trade-offs
* Requires HTTPS / secure origin for browser microphone access permissions.
* Raw PCM consumes 256 kbps bandwidth per active channel (mitigated by direct VPC networking and direct egress).
