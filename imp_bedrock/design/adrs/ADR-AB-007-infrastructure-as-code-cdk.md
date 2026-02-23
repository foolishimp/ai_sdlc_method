# ADR-AB-007: Infrastructure as Code via AWS CDK

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Bedrock Genesis Design Authors
**Requirements**: REQ-TOOL-001, REQ-TOOL-011

---

## Context

The Bedrock Genesis implementation deploys a non-trivial set of AWS services: Step Functions state machines (ADR-AB-001), Lambda functions (ADR-AB-002), DynamoDB tables (ADR-AB-005), EventBridge rules, API Gateway endpoints, S3 buckets, and Bedrock Knowledge Bases (ADR-AB-006). These resources must be provisioned consistently across environments (dev, staging, prod), be reproducible from source control, and support both single-project and multi-project deployments within a single AWS account.

The deployment also carries methodology-specific assets. `graph_topology.yml`, edge parameter files, and profile YAMLs must be deployed alongside the compute infrastructure so that the iterate engine can load them at runtime. This rules out purely manual or console-based provisioning.

Two deployment granularities are needed:

1. **Shared engine resources** that exist once per account/region -- the Step Functions state machine, common Lambda layers, the iterate orchestrator, EventBridge bus, and API Gateway.
2. **Per-project resources** that are instantiated for each project under management -- the project S3 bucket, Bedrock Knowledge Base, project-scoped DynamoDB partition, and project-specific Lambda environment configuration.

---

## Options Considered

### Option 1: Raw CloudFormation

Write CloudFormation templates directly in JSON or YAML.

- **Pros**: No additional tooling beyond the AWS CLI; templates are the native AWS deployment format.
- **Cons**: Extremely verbose; no type checking; no abstraction or composition mechanism; cross-stack references are manual and error-prone; no construct reuse across projects.

### Option 2: Terraform

Use HashiCorp Terraform with the AWS provider.

- **Pros**: Mature ecosystem; state management; multi-cloud capable; HCL is concise relative to raw CloudFormation.
- **Cons**: Non-AWS-native (separate state backend needed); provider lag behind new AWS features; HCL is a DSL with limited composability compared to a general-purpose language; no native CDK Pipelines equivalent for AWS-native CI/CD.

### Option 3: AWS CDK (TypeScript) -- CHOSEN

Use the AWS Cloud Development Kit with TypeScript to define infrastructure as code using L2 and L3 constructs.

- **Pros**: Type-safe definitions; composable constructs; native synthesis to CloudFormation; CDK Pipelines for CI/CD; L2/L3 abstractions reduce boilerplate by 60-80% relative to raw CloudFormation; npm package distribution for construct reuse; first-class support for all AWS services used by Bedrock Genesis.
- **Cons**: CDK version churn requires periodic dependency updates; `cdk synth` time grows with stack complexity; introduces a TypeScript build dependency into the infrastructure workflow.

---

## Decision

**We adopt AWS CDK (TypeScript) for all Bedrock Genesis infrastructure deployment (Option 3).**

### Two-Stack Architecture

The deployment is organized into two CDK constructs at different granularities:

#### 1. Shared Engine Stack (`BedrockGenesisEngineStack`)

Deployed once per AWS account/region. Contains:

- **Step Functions state machine** -- the iterate orchestrator (ADR-AB-001)
- **Lambda layers** -- shared runtime dependencies (Python packages, methodology libraries)
- **DynamoDB tables** -- `aisdlc-events` (event sourcing), `aisdlc-state` (workspace state), `aisdlc-features` (feature vectors)
- **EventBridge rules** -- event bus for cross-service integration and observer notifications
- **API Gateway** -- REST API for external integration (CI/CD triggers, status queries)
- **IAM roles** -- least-privilege execution roles for Lambda and Step Functions

#### 2. Per-Project Construct (`BedrockGenesisProjectConstruct`)

Instantiated once per managed project. Contains:

- **S3 bucket** -- project artifacts, configuration files, iterate outputs
- **Bedrock Knowledge Base** -- project-specific RAG index over codebase and documentation (ADR-AB-006)
- **Lambda environment configuration** -- project-scoped environment variables (project ID, S3 paths, Knowledge Base ID)
- **DynamoDB partition keys** -- project-scoped partitions within shared tables

### CDK Construct Library

The per-project construct is published as an npm package (`@bedrock-genesis/project-construct`) so that:

- New projects can be onboarded by importing the construct and providing project-specific parameters.
- Teams can extend the construct with project-specific overrides without forking.

### Configuration Injection

Methodology configuration files (`graph_topology.yml`, edge parameter YAMLs, profile YAMLs) are deployed to S3 as CDK assets:

```typescript
const topologyAsset = new s3assets.Asset(this, 'GraphTopology', {
  path: path.join(__dirname, '../config/graph_topology.yml'),
});
```

Lambda functions reference these assets via environment variables pointing to S3 URIs.

### Environment Promotion

Environment promotion follows a three-stage pipeline managed by CDK Pipelines (backed by AWS CodePipeline):

```
dev → staging → prod
```

Each stage deploys the shared engine stack and all registered per-project constructs. Manual approval gates are configured between staging and prod.

---

## Rationale

1. **Type safety**: TypeScript catches infrastructure misconfigurations at compile time rather than at deploy time. Step Functions ASL definitions, Lambda configurations, and IAM policies are all type-checked.
2. **Construct reuse**: The per-project construct encapsulates the repeatable infrastructure pattern. Adding a new project is a single construct instantiation, not a copy-paste of CloudFormation templates.
3. **Native AWS integration**: CDK synthesizes to CloudFormation, which is the native AWS deployment model. No external state backend is needed (unlike Terraform). CDK Pipelines uses CodePipeline natively.
4. **CI/CD via CDK Pipelines**: The pipeline itself is defined in CDK, meaning infrastructure CI/CD is version-controlled and reproducible alongside the application infrastructure.
5. **Asset management**: CDK's asset system handles uploading methodology YAML configs to S3 with content-addressable naming, ensuring Lambda functions always reference the correct configuration version.

---

## Consequences

### Positive

- Type-safe infrastructure definitions eliminate a class of deployment errors caught only at CloudFormation deploy time.
- Reusable construct library enables rapid onboarding of new projects with consistent infrastructure.
- Native AWS integration avoids external state management and provider version lag.
- CDK Pipelines provides a fully managed CI/CD pipeline for infrastructure promotion across environments.
- Configuration files are deployed as versioned assets, maintaining traceability between methodology config and deployed infrastructure.

### Negative

- CDK version churn: major CDK releases may require migration effort; mitigated by pinning CDK versions and scheduling periodic upgrades.
- Synth time: large stacks with many per-project constructs increase `cdk synth` duration; mitigated by caching and parallel synthesis where possible.
- TypeScript dependency: infrastructure engineers must be comfortable with TypeScript; mitigated by the fact that CDK TypeScript is idiomatic and well-documented.

### Mitigation

- Pin CDK version in `package.json`; upgrade quarterly with dedicated migration tickets.
- Monitor synth times; split into parallel stacks if synthesis exceeds 60 seconds.
- Provide CDK construct documentation and examples in the repository.

---

## References

- [ADR-AB-001](ADR-AB-001-bedrock-runtime-as-platform.md) -- Bedrock Runtime as Target Platform (Step Functions orchestration)
- [ADR-AB-002](ADR-AB-002-lambda-iterate-engine.md) -- Lambda-based Iterate Engine
- [ADR-AB-005](ADR-AB-005-dynamodb-event-sourcing.md) -- DynamoDB Event Sourcing
- [ADR-AB-006](ADR-AB-006-knowledge-base-rag.md) -- Bedrock Knowledge Base for RAG
- [BEDROCK_GENESIS_DESIGN.md](../BEDROCK_GENESIS_DESIGN.md)
- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md)
- [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../../specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) -- REQ-TOOL-001, REQ-TOOL-011
