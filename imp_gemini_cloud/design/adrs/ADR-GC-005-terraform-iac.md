# ADR-GC-005: Terraform for Infrastructure as Code

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Gemini Cloud Genesis Design Authors
**Requirements**: REQ-TOOL-001, REQ-TOOL-007
**Extends**: ADR-GC-001 (Vertex AI Platform)

---

## Context

Gemini Cloud Genesis requires orchestrating 10+ GCP services. Manual deployment is error-prone and non-reproducible. We need an industry-standard Infrastructure-as-Code (IaC) tool to manage the lifecycle of the methodology stack.

### Options Considered

1. **Deployment Manager**: GCP native, but lacks the broad ecosystem and provider support of Terraform.
2. **Pulumi**: Powerful, but requires a programming language (TS/Python). Terraform HCL is more common for platform engineering.
3. **Terraform (The Decision)**: Most widely used IaC tool for GCP. Excellent provider support for Workflows, Firestore, and Vertex AI.

---

## Decision

**We use Terraform to manage all Gemini Cloud Genesis infrastructure.**

The `code/` directory will include a `terraform/` module that defines:
- Cloud Workflows definitions.
- Artifact Registry for evaluator images.
- GCS Buckets for config and artifacts.
- Firestore collections and indexes.
- API Gateway and Cloud Functions.
- Service Accounts and IAM bindings.

---

## Rationale

### Reproducibility and Auditability
Using Terraform ensures that every project gets an identical methodology stack. Changes to the engine (e.g., adding a new monitor) are version-controlled and reviewed via Terraform plans.

---

## Consequences

### Positive
- **Standardised Stacks**: Consistent deployment across dev/staging/prod.
- **Dependency Management**: Terraform manages the creation order of inter-dependent GCP resources.

### Negative
- **State Management**: Requires a backend (like GCS) to store the Terraform state file.

---

## References

- [GEMINI_CLOUD_GENESIS_DESIGN.md](../GEMINI_CLOUD_GENESIS_DESIGN.md)
- [ADR-AB-007](../../imp_bedrock/design/adrs/ADR-AB-007-infrastructure-as-code-cdk.md) — AWS CDK equivalent
