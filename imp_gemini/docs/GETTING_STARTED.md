# Getting Started with Gemini CLI (v3.0)

**Version**: 3.0.2 | **Platform**: Gemini CLI | **Date**: 2026-03-11

This guide covers the full lifecycle of a Gemini-managed project, from installation to orchestrated execution and consensus-driven evaluation.

---

## 1. Installation

Gemini CLI is installed via a single-command bootstrap script that scaffolds your workspace.

### 1.1 One-Command Install
Run the following in your project root:

```bash
python3 gemini_cli/installers/gemini-setup.py --target .
```

This creates the `.ai-workspace/` directory with the following v3.0 structure:
- `events/`: The OpenLineage-compliant event ledger.
- `features/active/`: Feature vector YAMLs.
- `graph/`: Asset graph topology.
- `context/`: Project constraints and ADRs.

---

## 2. Your First Project

### 2.1 Initialize Workspace
If you didn't use the installer, or want to re-initialize:

```bash
python3 -m gemini_cli.cli init --name "my-awesome-project"
```

### 2.2 Create a Feature Vector
Spawn a new feature to track its trajectory through the graph:

```bash
python3 -m gemini_cli.cli spawn --id REQ-F-AUTH-001 --intent "Implement OAuth2 Login"
```

---

## 3. Executing the Deterministic Flow

The "Deterministic Flow" refers to executing transitions where `F_D` (deterministic) evaluators are primary (e.g., tests, linters, build checks).

### 3.1 Headless Iteration
Run a single edge transition without human intervention:

```bash
python3 -m gemini_cli.cli iterate --feature REQ-F-AUTH-001 --edge "design\u2192code" --asset src/auth.py --mode headless
```

In `headless` mode:
- The engine runs all configured functors (Agent, Deterministic).
- It will **not** pause for human feedback.
- It will converge if delta reaches 0.

### 3.2 Automated Orchestration
Use the `start` command to let Gemini detect the current state and select the next logical step:

```bash
python3 -m gemini_cli.cli start
```

This will output the recommended next action, which you can then execute.

---

## 4. The Consensus Observer Flow

The Consensus Observer is a homeostatic loop that reacts to stakeholder input (comments/votes) and drives the `ConsensusFunctor`.

### 4.1 Starting the Observer
Start the sensory service in loop mode to watch for external signals:

```bash
python3 -m gemini_cli.cli sense --loop --interval 30
```

The service will:
1. Scan `.ai-workspace/comments/` for new feedback.
2. Emit `comment_received` events.
3. Triage these signals to raise convergence intents.

### 4.2 Reacting to Comments
To provide feedback that the system will react to:

1. Create a comment file in `.ai-workspace/comments/comment_001.yml`:
   ```yaml
   author: "stakeholder_1"
   feature: "REQ-F-AUTH-001"
   edge: "requirements\u2192design"
   verdict: "reject"
   comment: "The proposed design misses the PKCE requirement for mobile clients."
   ```

2. The `sense` loop detects this file.
3. The `AffectTriageEngine` raises an intent.
4. The next `/gen-iterate` run for this edge will trigger the **Consensus Functor**, which aggregates these votes and blocks convergence until the delta (undispositioned comments) is resolved.

---

## 5. Command Reference Summary

| Command | Purpose |
|---------|---------|
| `init` | Bootstrap a new workspace |
| `spawn` | Create a new feature vector |
| `start` | Detect state and show next step |
| `status` | Show Hamiltonian metrics ($T, V, H$) and progress |
| `iterate` | Execute a transition edge |
| `sense` | Run the consensus observer / monitor loop |
| `review` | Handle human gates and feature proposals |

---

## Further Reading
- `docs/OPERATIONAL_MANIFESTO.md`: The philosophy of the Asset Graph.
- `design/AISDLC_V2_DESIGN.md`: Detailed architecture of the v3.0 engine.
