# ADR-012: Two-Command UX Layer — Bedrock Genesis Binding

**Status**: Accepted
**Date**: 2026-02-23
**Deciders**: Bedrock Genesis Design Authors
**Requirements**: REQ-UX-001 (State-Driven Routing), REQ-UX-002 (Progressive Disclosure), REQ-UX-003 (Project-Wide Observability), REQ-UX-004 (Routing Transparency), REQ-UX-005 (Escape Hatch)

---

## Context

The AI SDLC methodology exposes 9 commands (`gen-init`, `gen-iterate`, `gen-spawn`, `gen-status`, `gen-checkpoint`, `gen-review`, `gen-trace`, `gen-gaps`, `gen-release`). CLI implementations (Claude, Gemini, Codex) present these as slash commands in an interactive session. Dogfooding confirmed that the primary adoption barrier is cognitive load: users ask "Where am I?" and "What do I do next?" and should not need to learn 9 commands to get answers.

Bedrock Genesis operates as a **stateless, API-driven, serverless** system. There is no interactive terminal session. Entry points are HTTP endpoints (API Gateway), CLI tool invocations, or CI/CD webhook triggers. The two-command abstraction must bridge three distinct consumer surfaces:

1. **Developer CLI** — a thin wrapper calling API Gateway, providing the same conversational feel as `/gen-start` and `/gen-status` in CLI implementations.
2. **API consumers** — CI/CD pipelines, web dashboards, and integrations that call REST endpoints directly without CLI intermediation.
3. **Power users** — direct invocation of specific endpoint variants for fine-grained control (re-running a specific edge, manual spawn with custom profile).

The question is how to preserve the two-verb simplicity ("Go" and "Where am I?") while exposing the full command surface through a REST API.

### Options Considered

1. **API-only (no CLI)** — Expose all 9 commands as REST endpoints. Rely on curl/httpie for developer experience. No abstraction layer.
2. **CLI-only (no API)** — Build a CLI tool that embeds the routing logic locally. Status queries hit DynamoDB directly via AWS SDK. No shared API surface.
3. **API Gateway + CLI wrapper** — Two primary endpoints (`POST /api/start`, `GET /api/status`) backed by Lambda routers. CLI tool wraps these endpoints for developer ergonomics. All 9 commands available as additional endpoints for power users.
4. **GraphQL single endpoint** — One endpoint with queries (status, trace, gaps) and mutations (start, iterate, spawn). Flexible but adds schema complexity without clear benefit for a command-oriented model.

---

## Decision

**We adopt the API Gateway + CLI wrapper approach (Option 3). Two primary REST endpoints implement Start and Status. A thin CLI tool wraps these for developer ergonomics. All 9 commands are available as individual endpoints for power users and CI/CD systems.**

### Endpoint Mapping

| Methodology Command | REST Endpoint | HTTP Method | Backed By |
|:---|:---|:---|:---|
| `gen-start` | `/api/start` | POST | Lambda router -> Step Functions |
| `gen-status` | `/api/status` | GET | Lambda -> DynamoDB query |
| `gen-init` | `/api/init` | POST | Lambda -> DynamoDB + S3 scaffold |
| `gen-iterate` | `/api/iterate` | POST | Lambda -> Step Functions execution |
| `gen-spawn` | `/api/spawn` | POST | Lambda -> DynamoDB + Step Functions |
| `gen-checkpoint` | `/api/checkpoint` | POST | Lambda -> S3 snapshot |
| `gen-review` | `/api/review` | POST/GET | Lambda -> DynamoDB reviews table |
| `gen-trace` | `/api/trace` | GET | Lambda -> DynamoDB GSI query |
| `gen-gaps` | `/api/gaps` | GET | Lambda -> DynamoDB + Bedrock analysis |
| `gen-release` | `/api/release` | POST | Lambda -> S3 manifest |

### Start Endpoint (`POST /api/start`)

The Start Lambda implements the same state-machine routing logic as `/gen-start` in CLI implementations:

```
POST /api/start
{
  "project_id": "my-project",
  "feature": "REQ-F-AUTH-001",   // optional — auto-selected if omitted
  "profile": "standard",         // optional — default from project config
  "dry_run": false               // optional — show routing decision without executing
}

Lambda Router Logic:
1. Read DynamoDB events table → derive project state
2. Read DynamoDB features table → determine feature trajectory
3. Read S3 graph_topology.yml → determine valid next edges
4. Apply routing heuristic:
   - No project state → delegate to /api/init
   - Feature specified, edge converged → route to next edge via /api/iterate
   - Feature specified, all edges converged → suggest spawn or release
   - No feature specified → select highest-priority uncompleted feature
   - Stuck detection (iteration count > stuck_threshold) → suggest /api/review
5. Launch Step Functions execution for the selected edge
6. Return: { execution_id, feature, edge, routing_reason }
```

The `routing_reason` field satisfies REQ-UX-004 (selection reasoning displayed to user). The `dry_run` mode returns the routing decision without launching an execution, enabling CI/CD pre-flight checks.

### Status Endpoint (`GET /api/status`)

The Status Lambda implements project-wide observability:

```
GET /api/status?project_id=my-project&feature=REQ-F-AUTH-001&health=true

Lambda Logic:
1. Query DynamoDB events table → aggregate project state
2. Query DynamoDB features table → per-feature trajectory
3. Query Step Functions → active execution status
4. If health=true: check DynamoDB Streams lag, Lambda error rates, pending reviews
5. Return structured status response:
   {
     "project": { "edges_completed": 4, "edges_remaining": 6, "active_features": 2 },
     "features": [
       {
         "id": "REQ-F-AUTH-001",
         "current_edge": "design_code",
         "iteration": 3,
         "you_are_here": "design_code (iteration 3/5, 2 evaluators passed)"
       }
     ],
     "signals": [ ... ],
     "health": { "streams_lag_ms": 120, "pending_reviews": 1, "stale_claims": 0 }
   }
```

The "you are here" indicator satisfies REQ-UX-003 (project-wide observability). Feature-level filtering supports focused queries.

### CLI Wrapper

A thin Python CLI tool wraps the API Gateway endpoints:

```bash
# Two primary commands
gen-start --project my-project                    # POST /api/start
gen-status --project my-project                   # GET /api/status

# With options
gen-start --project my-project --feature REQ-F-AUTH-001 --dry-run
gen-status --project my-project --health --feature REQ-F-AUTH-001

# Power-user escape hatch (any endpoint)
gen-iterate --project my-project --edge design_code --feature REQ-F-AUTH-001
gen-review --project my-project --list
gen-trace --project my-project --req REQ-F-AUTH-001
```

The CLI tool handles:
- AWS credential resolution (IAM, SSO, environment variables)
- API Gateway URL discovery (from CDK outputs or environment variable)
- Response formatting (structured JSON for scripts, human-readable for terminal)
- Polling for async execution results (Step Functions execution status)

### CI/CD Integration

CI/CD systems call API Gateway directly without the CLI wrapper:

```yaml
# CodePipeline action (example)
- Name: IterateDesign
  ActionTypeId:
    Category: Invoke
    Provider: Lambda
  Configuration:
    FunctionName: gen-start-router
    UserParameters: '{"project_id": "my-project", "profile": "standard"}'

# GitHub Actions (example)
- name: Run iterate
  run: |
    curl -X POST "$API_GATEWAY_URL/api/start" \
      -H "Authorization: Bearer $AWS_SESSION_TOKEN" \
      -d '{"project_id": "my-project"}'
```

No CLI installation required. The API contract is the integration surface.

### Progressive Disclosure

Progressive disclosure (REQ-UX-002) is preserved through the tiered endpoint structure:

| User Level | Surface | Commands Used |
|:---|:---|:---|
| Newcomer | CLI wrapper | `gen-start`, `gen-status` (2 commands) |
| Intermediate | CLI wrapper | `gen-start`, `gen-status`, `gen-review`, `gen-trace` (4 commands) |
| Power user | CLI or direct API | All 9 endpoints, with explicit edge/feature parameters |
| CI/CD | API Gateway | `POST /api/start`, `GET /api/status`, webhook triggers |

---

## Rationale

### Why API Gateway + CLI (vs API-Only)

1. **Developer ergonomics** — Bare `curl` calls with JSON payloads and AWS auth headers are friction-heavy for interactive development. The CLI wrapper provides the same two-verb experience (`gen-start`, `gen-status`) as CLI implementations.
2. **Credential handling** — The CLI tool leverages the AWS SDK credential chain (IAM roles, SSO, environment variables) transparently. Direct API calls require manual token management.
3. **Response formatting** — Terminal-friendly output (colored status, progress bars, "you are here" indicators) versus raw JSON improves the developer feedback loop.

### Why API Gateway + CLI (vs CLI-Only)

1. **CI/CD integration** — CI/CD pipelines need HTTP endpoints, not CLI tools. An API-first design makes CI/CD a configuration concern, not a scripting exercise.
2. **Multi-consumer** — Web dashboards, Slack bots, monitoring tools, and other integrations consume the same API surface. A CLI-only approach forces every consumer to shell out to the CLI.
3. **Shared state** — API Gateway + Lambda + DynamoDB provides a single state plane accessible by all consumers. A CLI-only approach requires each developer to maintain local state or implement their own cloud sync.

### Why REST (vs GraphQL)

1. **Command-oriented model** — The 9 methodology commands are imperative actions, not data queries. REST's verb-per-resource model maps naturally. GraphQL's query/mutation distinction adds schema complexity without enabling new capabilities.
2. **Caching** — GET endpoints (`/api/status`, `/api/trace`, `/api/gaps`) are naturally cacheable via API Gateway response caching. GraphQL POST requests are not cacheable at the HTTP layer.
3. **Operational simplicity** — REST endpoints map 1:1 to Lambda functions with independent scaling, monitoring, and permissions. A single GraphQL resolver would create a monolithic Lambda handling all queries.

---

## Consequences

### Positive

- **Two-verb simplicity preserved** — Newcomers use `gen-start` and `gen-status` regardless of whether they invoke CLI or API. The cognitive model is identical to CLI implementations.
- **CI/CD-native** — API Gateway endpoints are callable from any CI/CD system via HTTP. No CLI installation, no shell scripting, no agent session management.
- **Progressive disclosure** — Three tiers (newcomer, power user, CI/CD) access the same underlying commands at increasing granularity.
- **Routing transparency** — The `routing_reason` field in Start responses and `dry_run` mode satisfy REQ-UX-004. Developers and CI/CD systems can inspect routing decisions before execution.
- **Cacheable status** — API Gateway response caching on `/api/status` reduces DynamoDB read costs for frequently-polled status dashboards.

### Negative

- **CLI tool maintenance** — The CLI wrapper is an additional artifact to package, version, and distribute. Unlike slash commands embedded in the agent session, it requires separate installation (pip/npm/binary).
- **Authentication complexity** — API Gateway authentication (IAM, Cognito, API keys) adds setup friction compared to CLI implementations where the developer is implicitly authenticated by the host agent session.
- **Latency overhead** — Every CLI invocation traverses API Gateway -> Lambda -> DynamoDB (and back). Cold starts add 100ms-2s. CLI implementations have zero network overhead for state queries.
- **Async execution model** — `gen-start` returns an execution ID, not a completed result. The CLI tool must poll Step Functions for completion. This is less immediate than CLI implementations where the agent iterates synchronously in the session.

### Mitigation

- **CLI distribution** — Package as a single Python package (`pip install gen-cli`) with minimal dependencies (boto3, click). Alternatively, distribute as a standalone binary via GitHub Releases.
- **Authentication** — Default to IAM authentication with AWS SSO. Document credential setup in `GETTING_STARTED.md`. Support API key fallback for simple setups.
- **Latency** — Use provisioned concurrency on the Start and Status Lambda functions. Cache DynamoDB reads where appropriate (status projections).
- **Async UX** — CLI tool supports `--wait` flag that polls Step Functions and streams progress events. Default behavior returns immediately with execution ID for CI/CD compatibility.

---

## References

- [ADR-AB-001](ADR-AB-001-bedrock-runtime-as-platform.md) — Platform binding (API Gateway as developer entry point)
- [ADR-AB-004](ADR-AB-004-human-review-api-gateway-callbacks.md) — Human review callbacks (review endpoint interaction)
- [ADR-008](../../imp_claude/design/adrs/ADR-008-universal-iterate-agent.md) — Universal Iterate Agent (Start delegates to iterate engine, does not replace it)
- [ADR-009](../../imp_claude/design/adrs/ADR-009-graph-topology-as-configuration.md) — Graph Topology as Configuration (Start reads topology from S3)
- [ADR-014](ADR-014-intentengine-binding.md) — IntentEngine Binding (Start routing is affect-aware; Status surfaces IntentEngine state)
- [BEDROCK_GENESIS_DESIGN.md](../BEDROCK_GENESIS_DESIGN.md) — Bedrock implementation design
- [AI_SDLC_ASSET_GRAPH_MODEL.md](../../specification/AI_SDLC_ASSET_GRAPH_MODEL.md) — Canonical model, section 7.5 (Event Sourcing), section 7.6 (Self-Observation)
- [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../specification/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) — Requirements baseline, section 11 (REQ-UX-001 through REQ-UX-005)
