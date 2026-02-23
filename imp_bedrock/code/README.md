# Bedrock Genesis -- AI SDLC Implementation

## Overview

AWS Bedrock cloud-native implementation of the AI SDLC Asset Graph Model (v2.8). All four primitives -- Graph, Iterate, Evaluators, Spec+Context -- are realised as managed AWS services with no long-running processes.

This implementation targets teams who want the AI SDLC methodology running as a serverless, always-on platform rather than a developer-local CLI tool.

## Architecture

| Primitive | AWS Service |
|-----------|------------|
| **Iterate engine** | Step Functions (state machine per edge traversal) |
| **Evaluators** | Lambda functions (one per evaluator type: human, agent, deterministic) |
| **Graph topology** | Configuration in S3 / DynamoDB (`graph_topology.yml`) |
| **Context management** | Bedrock Knowledge Bases (RAG over spec, design, code) |
| **Event sourcing** | DynamoDB Streams + DynamoDB tables |
| **Sensory service** | EventBridge rules + Lambda monitors |
| **Entry point** | API Gateway (REST) + CLI wrapper |
| **Human review** | API Gateway callbacks with approval tokens (ADR-AB-004) |
| **Infrastructure** | CDK (TypeScript) -- single `cdk deploy` (ADR-AB-007) |

## Directory Structure

```text
code/
├── agents/                    # Agent prompt templates (markdown)
├── commands/                  # Command definitions (13 commands)
│   ├── gen-start.md
│   ├── gen-status.md
│   └── ...
├── hooks/
│   └── on-edge-converged.sh   # Post-convergence hook
├── config/
│   ├── graph_topology.yml     # 10 asset types, 10 transitions
│   ├── evaluator_defaults.yml # Convergence criteria per evaluator type
│   ├── affect_triage.yml      # Signal classification + API Gateway review boundary
│   ├── sensory_monitors.yml   # EventBridge/Lambda/DynamoDB Streams monitors
│   ├── agent_roles.yml        # Bedrock agent role definitions
│   ├── feature_vector_template.yml
│   ├── project_constraints_template.yml
│   ├── edge_params/           # Per-edge parameterisations (10 YAML files)
│   └── profiles/              # Projection profiles (full, standard, poc, spike, hotfix, minimal)
└── README.md
```

## Configuration

| File | Purpose |
|------|---------|
| `graph_topology.yml` | Asset types and admissible transitions |
| `evaluator_defaults.yml` | Convergence thresholds per evaluator |
| `affect_triage.yml` | Sensory signal classification, escalation thresholds, API Gateway review boundary |
| `sensory_monitors.yml` | Interoceptive/exteroceptive monitors with EventBridge schedules and DynamoDB Stream triggers |
| `agent_roles.yml` | Bedrock agent configurations and IAM role mappings |
| `edge_params/*.yml` | Edge-specific iterate parameters (context sources, evaluator checklists) |
| `profiles/*.yml` | Named projection profiles controlling graph shape and convergence density |

## Prerequisites

- AWS account with Bedrock model access enabled (Claude 3.5 Haiku, Claude Sonnet)
- AWS CDK v2 (`npm install -g aws-cdk`)
- Python 3.11+
- Node.js 18+ (for CDK)
- AWS CLI configured (`aws configure`)

## Quick Start

```bash
# 1. Deploy the stack (placeholder — CDK stack not yet built)
cd imp_bedrock/infra
cdk deploy AisdlcBedrockStack

# 2. Invoke via CLI wrapper
aisdlc-bedrock start --project /path/to/project
aisdlc-bedrock status

# 3. Or invoke directly via API Gateway
curl -X POST https://<api-id>.execute-api.<region>.amazonaws.com/v1/start \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"project_path": "/path/to/project", "profile": "standard"}'
```

> **Note**: CDK stacks and Lambda functions are not yet implemented. The config files define the target architecture; infrastructure code will follow.

## Testing

```bash
# Run Bedrock implementation tests
pytest imp_bedrock/tests/ -v

# Run shared spec-level tests
pytest tests/ -v
```

## Relationship to Specification

The `specification/` directory at the repository root defines the shared, technology-agnostic contract (WHAT the system does). This implementation (`imp_bedrock/`) provides the platform-specific design and code (HOW it works on AWS). The spec is authoritative; the implementation conforms to its requirements.

## References

- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) -- formal system
- [BEDROCK_GENESIS_DESIGN.md](../design/BEDROCK_GENESIS_DESIGN.md) -- platform design
- [ADRs (ADR-AB-001 through ADR-AB-008)](../design/adrs/) -- platform-specific architecture decisions
- [FEATURE_VECTORS.md](../../specification/FEATURE_VECTORS.md) -- feature decomposition
- [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) -- 67 platform-agnostic requirements
