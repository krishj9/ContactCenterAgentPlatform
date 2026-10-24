# Operational Runbook: Vertex AI Model Rollback

This runbook documents procedures for rolling back the active Vertex AI intent classification model or knowledge base index alias when canary validation gates fail.

---

## 1. Intent Model Instant Rollback

If a newly promoted `challenger` model exhibits elevated error rates, unexpected entropy, or accuracy degradation in production:

### Instant Traffic Split Rollback (Zero Downtime)
Execute the promotion pipeline rollback command to shift 100% of production inference traffic back to `champion`:

```bash
uv run python ml/pipelines/promote_intent.py \
  --project-id=${PROJECT_ID} \
  --region=us-central1 \
  --endpoint-id=${INTENT_ENDPOINT_ID} \
  --rollback-to-champion
```

Or via `gcloud`:
```bash
gcloud ai endpoints set-traffic-split ${INTENT_ENDPOINT_ID} \
  --project=${PROJECT_ID} \
  --region=us-central1 \
  --traffic-split=${CHAMPION_DEPLOYED_MODEL_ID}=100,${CHALLENGER_DEPLOYED_MODEL_ID}=0
```

---

## 2. Knowledge Base Alias Rollback

If a newly deployed knowledge base index contains corrupted chunks or policy inaccuracies:

1. **Revert Active KB Version Pointer**:
   ```bash
   uv run python pipeline/jobs/kb_promote.py \
     --manifest-path=data/manifest.json \
     --rollback-to-previous
   ```
2. **Purge Redis Policy Query Cache**:
   ```bash
   gcloud redis instances purge-keys ${REDIS_INSTANCE_ID} \
     --region=us-central1 \
     --keys="policy:*"
   ```
3. **Verify Retrieval Gate Passes**:
   ```bash
   uv run pytest backend/tests/eval/test_retrieval_eval.py -v
   ```
