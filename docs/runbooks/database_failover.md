# Operational Runbook: Cloud SQL Database Failover & Recovery

This runbook covers planned and emergency failovers for Cloud SQL PostgreSQL 16 (pgvector) high-availability instances.

---

## 1. High-Availability Architecture

* **Primary Instance**: `cc-postgres-prod` located in zone `us-central1-a`.
* **Standby Instance**: Synchronous standby located in zone `us-central1-c` with automatic zero-data-loss failover.
* **Read Replica**: `cc-postgres-prod-replica-1` handling heavy analytics and evaluation workloads.

---

## 2. Emergency Failover Procedure

When primary instance hardware fails or multi-zone network partitioning occurs:

1. **Initiate Forced Failover**:
   ```bash
   gcloud sql instances failover cc-postgres-prod \
     --project=${PROJECT_ID}
   ```
2. **Verify Failover Completion**:
   ```bash
   gcloud sql operations list --instance=cc-postgres-prod --limit=5
   ```
3. **Validate PgBouncer Connection Pool Recovery**:
   * Cloud Run instances will automatically reconnect via the internal Private IP address.
   * Verify database connections are active:
     ```bash
     curl -s https://${API_GATEWAY_URL}/health | jq .db_connected
     ```

---

## 3. Read Replica Promotion (Disaster Recovery)

If the primary cluster is irrecoverable:
```bash
# Promote read replica to standalone primary
gcloud sql instances promote-replica cc-postgres-prod-replica-1 \
  --project=${PROJECT_ID}

# Update Secret Manager database connection string to point to promoted replica IP
gcloud secrets versions add cc-database-url \
  --data-file=/path/to/new_connection_string.txt \
  --project=${PROJECT_ID}
```
