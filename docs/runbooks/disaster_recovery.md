# Operational Runbook: Disaster Recovery & Continuity

This runbook outlines the recovery plans to achieve Recovery Point Objective (**RPO < 15 minutes**) and Recovery Time Objective (**RTO < 60 minutes**) in the event of catastrophic data center or regional outages.

---

## 1. Backup Schedule & Retention Architecture

| Component | Backup Method | Frequency | Retention Period | Storage Location |
|---|---|---|---|---|
| **Cloud SQL PostgreSQL** | Automated PITR + Daily Snapshots | Continuous WAL + Daily 02:00 UTC | 30 Days | Dual-Region Cloud Storage (US) |
| **Audit Logs** | Immutable Log Sink | Real-time Streaming | 365 Days (Locked) | `cc-audit-compliance-locked` bucket |
| **Vector Policy Corpus** | Git-anchored Markdown + Manifest | On commit | Permanent | Git Repository + GCS CMEK Bucket |
| **Model Registry** | Vertex AI Model Registry Artifacts | On model promotion | Permanent | Regional CMEK GCS Bucket |

---

## 2. Regional Disaster Recovery Sequence (Cross-Region Restore)

If region `us-central1` experiences a catastrophic regional failure, restore to secondary region `us-east4`:

### Step 1: Deploy Terraform Infrastructure to Secondary Region
```bash
terraform -chdir=infra/terraform/envs/dr init
terraform -chdir=infra/terraform/envs/dr apply \
  -var="region=us-east4" \
  -var="env=dr"
```

### Step 2: Restore PostgreSQL Database from Point-in-Time Recovery
```bash
gcloud sql instances clone cc-postgres-prod cc-postgres-dr \
  --project=${PROJECT_ID} \
  --point-in-time="$(date -u -v-15M +'%Y-%m-%dT%H:%M:%SZ')"
```

### Step 3: Populate Policy Embeddings & Rebuild HNSW Index
```bash
uv run python pipeline/jobs/kb_build.py \
  --project-id=${PROJECT_ID} \
  --region=us-east4 \
  --profile=gcp
```

### Step 4: Update Global Cloud DNS / Load Balancer Backends
```bash
gcloud compute backend-services update cc-api-gateway-backend \
  --global \
  --add-backends=projects/${PROJECT_ID}/regions/us-east4/serverlessNegs/cc-api-neg-dr
```
