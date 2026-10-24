# Operational Runbook: High-Latency Troubleshooting

This runbook guides engineers in diagnosing and mitigating p95 latency spikes (> 2.5s) in end-to-end recommendation delivery.

---

## 1. Latency Budget & Span Breakdown

End-to-end assist recommendations must complete within **2,500ms** (p95) per Technical Specification §5.4:

| Span Name | Target (p95) | Warning Threshold | Escalation Action |
|---|---|---|---|
| `ws.audio_receive` | < 50ms | > 150ms | Inspect network egress and packet retransmissions |
| `stt.transcribe_turn` | < 450ms | > 800ms | Scale Cloud Speech-to-Text V2 streaming instances |
| `intent.classify` | < 60ms | > 150ms | Autoscale Vertex AI L4 GPU endpoint nodes |
| `rag.vector_retrieval` | < 80ms | > 200ms | Scale PgBouncer pool or tune HNSW `ef_search` |
| `llm.gemini_generate` | < 1,400ms | > 2,000ms | Switch to fallback model alias or regional endpoint |

---

## 2. Diagnostic Procedure

### Step 1: Isolate Slow Spans via Cloud Trace
Run the following gcloud command to fetch slowest traces in the past 30 minutes:
```bash
gcloud logging read \
  'resource.type="cloud_run_revision" AND jsonPayload.duration_ms > 2500' \
  --limit 20 \
  --format="json(timestamp,jsonPayload.trace_id,jsonPayload.span_name,jsonPayload.duration_ms)"
```

### Step 2: Remediating Vertex AI GPU Saturation
If `intent.classify` exceeds 150ms:
```bash
# Check current endpoint utilization
gcloud ai endpoints describe ${INTENT_ENDPOINT_ID} \
  --project=${PROJECT_ID} \
  --region=us-central1

# Scale min replicas to absorb traffic spike
gcloud ai endpoints mutate-deployed-model ${INTENT_ENDPOINT_ID} \
  --deployed-model-id=${DEPLOYED_MODEL_ID} \
  --min-replica-count=4 \
  --max-replica-count=10
```

### Step 3: Remediating Cloud SQL pgvector Contention
If `rag.vector_retrieval` exceeds 200ms:
1. Inspect active locks and long-running queries:
   ```sql
   SELECT pid, now() - query_start AS duration, query, state
   FROM pg_stat_activity
   WHERE state != 'idle' AND now() - query_start > interval '2 seconds';
   ```
2. Verify HNSW index memory residency in shared buffers:
   ```sql
   SELECT c.relname, pg_size_pretty(pg_relation_size(c.oid)) as size,
          count(*) as buffered_pages
   FROM pg_buffercache b
   JOIN pg_class c ON b.relfilenode = pg_relation_filenode(c.oid)
   WHERE c.relname LIKE '%hnsw%'
   GROUP BY c.relname, c.oid;
   ```
3. If memory pressure is high, scale Cloud SQL instance to `db-custom-16-65536`.
