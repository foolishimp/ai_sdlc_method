# /aisdlc-iterate - Invoke the Universal Iteration Function

Run one iteration of `iterate(Asset, Context[], Evaluators)` on a specific graph edge.

<!-- Implements: REQ-ITER-001, REQ-ITER-002 -->

## Usage

```
/aisdlc-iterate --edge "{source}→{target}" --feature "REQ-F-{DOMAIN}-{SEQ}" [--auto]
```

| Option | Description |
|--------|-------------|
| `--edge` | The graph transition to traverse (e.g., "design→code", "code↔unit_tests") |
| `--feature` | The feature vector (REQ-F-*) being worked on |
| `--auto` | Auto-iterate until convergence (skip human review on non-human edges) |

## Instructions

This command is the primary workflow action. It invokes the iterate agent on a specific edge of the asset graph.

### Step 1: Validate Edge

1. Read `.ai-workspace/graph/graph_topology.yml`
2. Verify the requested edge exists in the `transitions` section
3. If not found, list available transitions and ask the user to choose

### Step 2: Load Context

1. Load the edge parameterisation from `.ai-workspace/graph/edges/{edge_config}`
2. Load relevant Context[] from `.ai-workspace/context/`
3. Load the current asset state from the feature vector file
4. Record the current context hash for spec reproducibility

### Step 3: Invoke Iterate Agent

Pass to the `aisdlc-iterate` agent:
- The current asset (from the feature vector's trajectory)
- The loaded Context[]
- The edge parameterisation (evaluators, convergence criteria, guidance)

### Step 4: Process Results

1. Update the feature vector tracking file:
   - Increment iteration count
   - Record evaluator results
   - Record context hash
   - Update status (iterating | converged | blocked)

2. If human evaluator required:
   - Present the candidate for review
   - Record approval/rejection/feedback

3. If converged:
   - Report convergence
   - Update feature vector status
   - Show next available transitions

4. If not converged:
   - Report delta (what's still needed)
   - If `--auto`: re-invoke iterate
   - If not auto: wait for user to re-invoke

### Step 5: Show Iteration Report

```
ITERATION REPORT
================
Edge:       {source} → {target}
Feature:    {REQ-F-*}
Iteration:  {n}

Evaluators:
  Agent:          {PASS | FAIL: details}
  Deterministic:  {PASS | FAIL: details}
  Human:          {APPROVED | PENDING | REJECTED}

Delta: {what remains}
Status: {CONVERGED | ITERATING | BLOCKED}

Next: {suggested action}
```

## Examples

```bash
# Generate requirements from intent
/aisdlc-iterate --edge "intent→requirements" --feature "REQ-F-AUTH-001"

# Generate design from requirements
/aisdlc-iterate --edge "requirements→design" --feature "REQ-F-AUTH-001"

# TDD co-evolution (code + tests)
/aisdlc-iterate --edge "code↔unit_tests" --feature "REQ-F-AUTH-001"

# Auto-iterate code generation until tests pass
/aisdlc-iterate --edge "code↔unit_tests" --feature "REQ-F-AUTH-001" --auto
```
