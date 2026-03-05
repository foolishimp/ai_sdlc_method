# STRATEGY: From Black-Box Subprocesses to OTLP-Native Actors

**Author**: Gemini
**Date**: 2026-03-05T17:00:00Z
**Addresses**: `imp_claude` subprocess stalls, heartbeat implementation, robust self-healing
**For**: claude, all

## Summary
Shift the methodology's verification model from "Black-Box Subprocess Scraping" (monitoring pytest stdout dots) to "OTLP-Native Actor Heartbeats." This transition resolves the fragile buffering issues seen in current logs and enables true self-healing through structural observability.

## The Problem: Black-Box Observability
Current logs show an attempt to infer "life" by monitoring a pipe for character-level output (`pytest` dots). This is three layers of abstraction away from the work and is vulnerable to OS-level buffering (`PYTHONUNBUFFERED` conflicts). This results in 10-minute "blind" timeouts that kill productivity and prevent robust self-healing.

## The Solution: The "Transparent Actor" Model

### 1. Structural Heartbeats (OTLP)
Instead of counting seconds between stdout bytes, the verification engine must treat every constraint check as an **Observable Actor Action**.
- **Heartbeat = Span Duration**: A "living" task is one that is currently emitting a Span or sub-events. 
- **Structure**: Replace a single 20-minute `pytest` subprocess with a series of sequenced or parallel **Evaluator Spans**.
- **Visibility**: Use the OTLP/Phoenix stack to see the "Internal Pulse" of the actor in real-time.

### 2. Verification as Constraint Actors
`pytest` is a legacy tool, not the goal. For critical tasks, verification should move toward **Constraint-Based Actors**:
- **Discrete Checks**: Each requirement (REQ key) should be verified by a specific Evaluator Actor.
- **Immediate Feedback**: If a check fails, it emits a `finding_raised` event immediately, without waiting for a full "test suite" to complete.

### 3. Homeostasis (Self-Healing)
Self-healing is a function of the **Asset Graph**, not the subprocess manager.
- **Sensing**: The OTLP collector detects a "Silence Gap" (Stall) or an "Error Status" (Failure).
- **Triage**: The `affect_triage` logic classifies the signal.
- **Recovery**: Instead of a blind retry, the system **spawns** a targeted recovery vector (e.g., `vector_type: hotfix`) to address the specific delta detected.

## Recommended Action for imp_claude
1. **Abandon the Pipe-Scraper**: Stop trying to fix `subprocess.PIPE` buffering for `pytest` output.
2. **Instrument the Functors**: Update `fd_evaluate.py` to emit an OTLP Span for every check *internally*, rather than wrapping the whole process in a watchdog.
3. **Link to Phoenix**: Point Claude's execution to the live Phoenix instance (`localhost:6006`) to provide it with "Interoception"—the ability to see its own progress and stalls structurally.
