# ADR-003: Hybrid Vector Search using PostgreSQL 16 pgvector

* **Status**: Accepted
* **Date**: 2026-10-23
* **Deciders**: Architecture Review Board
* **Context**: Technical Specification §2.3, Checkpoint D4

---

## Context & Problem Statement
The knowledge retrieval subsystem must search across authored banking policies and 1,700+ FAQ documents with high precision and strict lineage tracking. Specialized external vector databases (Pinecone, Milvus, Weaviate) introduce multi-cloud operational complexity, separate backup regimes, and split-brain transactions between vector embeddings and relational audit metadata.

Furthermore, semantic dense vector search alone frequently fails on exact regulatory identifiers (e.g., `REG-E-104`, `FDIC-INS-02`, fee schedules), whereas pure keyword search misses paraphrased customer requests.

## Decision
We standardized on **PostgreSQL 16 with the `pgvector` extension** as our unified vector store across both local Docker Compose and production Cloud SQL:
1. **Hybrid Retrieval**: Combines dense semantic search (768-dimensional embeddings indexed via **HNSW**) with sparse lexical search (**tsvector** full-text search with English stemming).
2. **Reciprocal Rank Fusion (RRF)**: Merges dense and sparse ranks with a constant parameter $k=60$:
   $$\text{RRF Score}(d) = \frac{1}{60 + r_{\text{dense}}(d)} + \frac{1}{60 + r_{\text{sparse}}(d)}$$
3. **Cross-Encoder Reranking**: The top 20 candidates are reranked via Vertex AI Ranking API / cross-encoder to select the final top-5 context chunks.

## Consequences

### Positive
* **ACID Consistency**: Policy chunks, relational audit event chains, and vector embeddings reside in the same PostgreSQL transaction boundary.
* **Unified Tooling**: Backups, point-in-time recovery (PITR), CMEK encryption, and Alembic migrations operate seamlessly across relational and vector tables.
* **Local Parity**: Developers run identical queries locally in Docker Compose (`pgvector/pgvector:pg16`) as in Cloud SQL PostgreSQL.

### Negative / Trade-offs
* Requires appropriate RAM sizing (`db-custom-8-32768`) to keep HNSW index structures hot in `shared_buffers`.
