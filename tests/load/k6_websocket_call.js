/**
 * k6 High-Concurrency WebSocket Load Testing Script (Spec §7.1, Phase P10.6).
 *
 * Simulates 500 concurrent live customer/agent voice and assist sessions over WebSockets,
 * measuring p95 recommendation latency (< 2.5s), connection stability, and error rates.
 *
 * Usage:
 *   k6 run --vus 500 --duration 5m tests/load/k6_websocket_call.js
 */

import ws from 'k6/ws';
import { check, sleep } from 'k6';
import { Trend, Rate, Counter } from 'k6/metrics';

// Custom Golden Signal Metrics
const recommendationLatency = new Trend('recommendation_latency_ms');
const intentLatency = new Trend('intent_latency_ms');
const sessionDropRate = new Rate('session_drop_rate');
const messagesReceived = new Counter('messages_received');

export const options = {
  scenarios: {
    live_call_sessions: {
      executor: 'ramping-vus',
      startVUs: 10,
      stages: [
        { duration: '30s', target: 100 },  // Ramp-up to 100 VUs
        { duration: '1m', target: 500 },   // Ramp-up to 500 VUs
        { duration: '3m', target: 500 },   // Soak test at 500 concurrent sessions
        { duration: '30s', target: 0 },    // Ramp-down
      ],
    },
  },
  thresholds: {
    'recommendation_latency_ms': ['p(95)<2500', 'p(99)<4000'], // p95 < 2.5s per Spec §5.4
    'intent_latency_ms': ['p(95)<250'],                          // p95 < 250ms for intent
    'session_drop_rate': ['rate<0.01'],                          // Drop rate < 1%
    'ws_connecting': ['p(95)<500'],                              // Handshake < 500ms
  },
};

const BASE_URL = __ENV.WS_URL || 'ws://localhost:8000/ws';

export default function () {
  const sessionId = `load_sess_${__VU}_${Date.now()}`;
  const participantId = `agent_${__VU}`;
  const url = `${BASE_URL}?session_id=${sessionId}&participant_id=${participantId}&role=agent`;

  const params = {
    tags: { scenario: 'live_call' },
  };

  const res = ws.connect(url, params, function (socket) {
    let turnCount = 0;
    let turnStartTime = 0;

    socket.on('open', () => {
      // 1. Send simulated join / customer speech transcript
      const initialUtterance = {
        event_type: 'transcript.final',
        session_id: sessionId,
        turn_id: 1,
        speaker: 'customer',
        text: 'My debit card was declined at the grocery store checkout. Can you unlock it?',
        timestamp: new Date().toISOString(),
      };

      turnStartTime = Date.now();
      socket.send(JSON.stringify(initialUtterance));
    });

    socket.on('message', (data) => {
      messagesReceived.add(1);
      try {
        const msg = JSON.parse(data);

        // Record intent classification latency
        if (msg.event_type === 'issue.update') {
          const lat = Date.now() - turnStartTime;
          intentLatency.add(lat);
        }

        // Record recommendation generation latency
        if (msg.event_type === 'assist.recommendation') {
          const lat = Date.now() - turnStartTime;
          recommendationLatency.add(lat);
          turnCount += 1;

          // Simulate follow-up turn after agent review
          if (turnCount < 3) {
            sleep(2);
            turnStartTime = Date.now();
            const followUp = {
              event_type: 'transcript.final',
              session_id: sessionId,
              turn_id: turnCount * 2,
              speaker: 'customer',
              text: 'Yes, please confirm and place a 24-hour override on the card.',
              timestamp: new Date().toISOString(),
            };
            socket.send(JSON.stringify(followUp));
          } else {
            // Close session gracefully after completed dialogue
            socket.close();
          }
        }
      } catch (err) {
        // Parse error
      }
    });

    socket.on('close', () => {
      sessionDropRate.add(0);
    });

    socket.on('error', (e) => {
      sessionDropRate.add(1);
    });

    // Timeout session after 60 seconds
    socket.setTimeout(() => {
      socket.close();
    }, 60000);
  });

  check(res, { 'status is 101': (r) => r && r.status === 101 });
}
