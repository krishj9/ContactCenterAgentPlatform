# ADR-008: VPC Service Controls & Customer-Managed Encryption Keys (CMEK)

* **Status**: Accepted
* **Date**: 2026-10-23
* **Deciders**: Architecture Review Board & Security Architecture
* **Context**: Technical Specification §6.1, Phase P10.1, P10.2

---

## Context & Problem Statement
Financial institutions operating contact center platforms must adhere to strict data residency and perimeter protection standards (PCI-DSS, SOC 2 Type II, GLBA). Relying solely on Google-managed encryption keys and public API routing exposes the platform to potential data exfiltration via compromised credentials or misconfigured storage buckets.

## Decision
We implemented a zero-trust enterprise security posture combining **VPC Service Controls (VPC-SC)** and **Cloud KMS Customer-Managed Encryption Keys (CMEK)**:
1. **Cryptographic Perimeter (VPC-SC)**:
   * A service perimeter (`infra/terraform/modules/vpc_sc`) encloses all data, AI, and persistence services: Cloud Run, Cloud SQL, Vertex AI, Cloud Storage, and BigQuery.
   * Restricts data movement across perimeter boundaries, blocking data exfiltration even if service account keys are compromised.
2. **Customer-Managed Encryption Keys (CMEK)**:
   * Dedicated Cloud KMS Key Rings (`infra/terraform/modules/kms`) provision distinct CryptoKeys with automated 90-day rotation (`rotation_period = 7776000s`) for:
     * Cloud SQL PostgreSQL database
     * Cloud Storage buckets (audit compliance and model registry)
     * Vertex AI custom training and endpoints
     * BigQuery audit log tables
3. **IAM Least Privilege**: Cryptographic access is granted only to the specific Google-managed service identities with `roles/cloudkms.cryptoKeyEncrypterDecrypter`.

## Consequences

### Positive
* **Full Data Ownership**: The bank retains complete cryptographic authority over data at rest; disabling a KMS key instantly renders all databases and models inaccessible.
* **Exfiltration Immunity**: VPC-SC prevents copying data to storage buckets or datasets outside the defined organizational boundary.

### Negative / Trade-offs
* Terraform provisioning requires Access Context Manager access policy administrative privileges.
