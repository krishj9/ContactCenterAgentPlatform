/**
 * Resilient WebSocket client with exponential backoff reconnection,
 * message buffering, packet sequence tracking, and binary audio frame streaming.
 */

import { createTraceparent } from "../telemetry/otel";
import type { InboundEvent, OutboundEvent } from "../types/contracts";

export type ConnectionState = "idle" | "connecting" | "connected" | "disconnected" | "error";

export interface WebSocketClientOptions {
  sessionId: string;
  role: "customer" | "agent";
  participantId: string;
  token?: string | null;
  serverUrl?: string;
  autoConnect?: boolean;
  maxReconnectDelayMs?: number;
}

type EventListener<T = OutboundEvent> = (event: T) => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private state: ConnectionState = "idle";
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private outgoingQueue: (string | ArrayBuffer)[] = [];
  private listeners: Map<string, Set<EventListener<any>>> = new Map();
  private stateChangeListeners: Set<(state: ConnectionState) => void> = new Set();

  public readonly sessionId: string;
  public readonly role: "customer" | "agent";
  public readonly participantId: string;
  public token: string | null;
  private readonly serverUrl: string;
  private readonly maxReconnectDelayMs: number;
  private isExplicitlyClosed = false;

  constructor(options: WebSocketClientOptions) {
    this.sessionId = options.sessionId;
    this.role = options.role;
    this.participantId = options.participantId;
    this.token = options.token || null;
    this.maxReconnectDelayMs = options.maxReconnectDelayMs || 10000;

    // Resolve base WS URL
    if (options.serverUrl) {
      this.serverUrl = options.serverUrl;
    } else {
      const isSecure = typeof window !== "undefined" && window.location.protocol === "https:";
      const host = typeof window !== "undefined" ? window.location.hostname : "localhost";
      const port = "8000";
      this.serverUrl = `${isSecure ? "wss" : "ws"}://${host}:${port}`;
    }

    if (options.autoConnect) {
      this.connect();
    }
  }

  public getState(): ConnectionState {
    return this.state;
  }

  private setState(newState: ConnectionState) {
    if (this.state !== newState) {
      this.state = newState;
      this.stateChangeListeners.forEach((listener) => listener(newState));
    }
  }

  public onStateChange(listener: (state: ConnectionState) => void): () => void {
    this.stateChangeListeners.add(listener);
    listener(this.state);
    return () => this.stateChangeListeners.delete(listener);
  }

  public on<T extends OutboundEvent>(eventType: T["type"] | "*", listener: EventListener<T>): () => void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType)!.add(listener);

    return () => {
      const set = this.listeners.get(eventType);
      if (set) {
        set.delete(listener);
        if (set.size === 0) {
          this.listeners.delete(eventType);
        }
      }
    };
  }

  public connect(): void {
    if (this.ws && (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN)) {
      return;
    }

    this.isExplicitlyClosed = false;
    this.setState("connecting");

    const query = new URLSearchParams({
      role: this.role,
      participant_id: this.participantId,
      traceparent: createTraceparent(),
    });
    if (this.token) {
      query.set("token", this.token);
    }

    const wsUrl = `${this.serverUrl}/ws/session/${encodeURIComponent(this.sessionId)}?${query.toString()}`;

    try {
      this.ws = new WebSocket(wsUrl);
      this.ws.binaryType = "arraybuffer";

      this.ws.onopen = () => {
        this.setState("connected");
        this.reconnectAttempts = 0;
        this.startHeartbeat();
        this.flushQueue();
      };

      this.ws.onmessage = (event: MessageEvent) => {
        if (typeof event.data === "string") {
          try {
            const parsed = JSON.parse(event.data) as OutboundEvent;
            this.dispatch(parsed);
          } catch {
            // Non-JSON or raw text
          }
        }
      };

      this.ws.onerror = () => {
        this.setState("error");
      };

      this.ws.onclose = (event) => {
        this.stopHeartbeat();
        this.ws = null;
        this.setState("disconnected");

        // Do not auto-reconnect if policy violation (e.g. invalid token) or explicitly closed
        if (!this.isExplicitlyClosed && event.code !== 1008) {
          this.scheduleReconnect();
        }
      };
    } catch {
      this.setState("error");
      this.scheduleReconnect();
    }
  }

  private dispatch(event: OutboundEvent): void {
    const specificListeners = this.listeners.get(event.type);
    if (specificListeners) {
      specificListeners.forEach((fn) => fn(event));
    }
    const wildcardListeners = this.listeners.get("*");
    if (wildcardListeners) {
      wildcardListeners.forEach((fn) => fn(event));
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) return;

    // Exponential backoff: 500ms, 750ms, 1125ms... capped at maxReconnectDelayMs
    const delay = Math.min(
      this.maxReconnectDelayMs,
      500 * Math.pow(1.5, this.reconnectAttempts)
    );
    this.reconnectAttempts++;

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, delay);
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        // Ping
        try {
          this.ws.send(JSON.stringify({ type: "ping", timestamp: new Date().toISOString() }));
        } catch {
          // ignore
        }
      }
    }, 25000);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private flushQueue(): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;

    while (this.outgoingQueue.length > 0) {
      const item = this.outgoingQueue.shift();
      if (item) {
        try {
          this.ws.send(item);
        } catch {
          this.outgoingQueue.unshift(item);
          break;
        }
      }
    }
  }

  public send(event: InboundEvent): void {
    const payload = JSON.stringify(event);
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(payload);
    } else {
      this.outgoingQueue.push(payload);
    }
  }

  public sendAudioChunk(pcmBuffer: ArrayBuffer, sequence: number): void {
    // Construct binary envelope:
    // Magic: 2 bytes (0xCC, 0x01)
    // Seq: 4 bytes uint32
    // Role: 1 byte (1 = customer, 2 = agent)
    // Audio PCM: remainder
    const headerSize = 7;
    const totalLength = headerSize + pcmBuffer.byteLength;
    const packet = new Uint8Array(totalLength);

    packet[0] = 0xcc;
    packet[1] = 0x01;

    // uint32 big-endian sequence
    const view = new DataView(packet.buffer);
    view.setUint32(2, sequence, false);

    // role
    packet[6] = this.role === "customer" ? 1 : 2;

    // copy PCM bytes
    packet.set(new Uint8Array(pcmBuffer), headerSize);

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(packet.buffer);
    }
    // Note: dropped audio frames are not buffered to preserve live real-time latency
  }

  public disconnect(): void {
    this.isExplicitlyClosed = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.stopHeartbeat();

    if (this.ws) {
      this.ws.close(1000, "Normal Closure");
      this.ws = null;
    }
    this.setState("disconnected");
  }
}
