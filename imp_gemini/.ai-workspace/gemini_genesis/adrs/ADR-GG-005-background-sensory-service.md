# ADR-GG-005: Background Sensory Service via Tooling

**Status**: Accepted
**Date**: 2026-02-21
**Deciders**: Gemini CLI Agent
**Requirements**: REQ-SENSE-001 through REQ-SENSE-005

---

## Context

The Asset Graph Model specifies a **Sensory Service** that runs continuous "Interoceptive" and "Exteroceptive" monitors to maintain project homeostasis. In the Claude implementation, this is designed as a separate MCP Server (Model Context Protocol) which provides a persistent connection.

Gemini CLI lacks a direct "Plugin-as-a-Service" model but has the powerful `run_shell_command` tool with an `is_background` parameter. We need to decide how to implement the background monitoring required for the Sensory Service in Gemini.

### Options Considered

1.  **Polling-based Sensing**: Run sensors only when the user invokes the `aisdlc_status` tool.
2.  **Background "Watcher" Process**: Use `run_shell_command(is_background=true)` to launch a lightweight Python script that monitors the workspace in the background.
3.  **External Server (matching Claude)**: Require the user to manually launch an external monitoring server and connect via a socket.

---

## Decision

**We will implement the Sensory Service as a native background "Watcher" script launched via the `aisdlc_sense` Tool.**

Workflow:
1.  **Launch**: On project startup (or manually by user), the `aisdlc_sense` tool is called.
2.  **Backgrounding**: The Tool uses `run_shell_command("python3 .ai-workspace/scripts/sense.py", is_background=true)`.
3.  **Monitoring**: The script watches for file changes (e.g., in `events.jsonl`) and runs scheduled exteroceptive checks (e.g., CVE audits).
4.  **Signal Generation**: When a deviation is detected, the script appends an `interoceptive_signal` or `exteroceptive_signal` event to `events.jsonl`.
5.  **Notification**: The Gemini Agent reads these new events in the next turn and surfaces them to the user.

---

## Rationale

### Why Background Watcher (vs Polling)

1.  **Real-time Responsiveness**: Polling only catches issues when the user asks. A background watcher can detect a CVE vulnerability or a test failure the moment the file is saved/audited.
2.  **Native Simplicity**: It utilizes Gemini's built-in capability to manage subprocesses without requiring an external protocol like MCP.
3.  **Cross-Platform Consistency**: A Python-based watcher script is easily portable across developer OSs (macOS, Linux, Windows).
4.  **Decoupled Lifecycle**: The sensor can run independently of the interactive Gemini CLI session, allowing for "async homeostasis" where the system senses while the developer is away.

---

## Consequences

### Positive

-   **Autonomous Homeostasis**: The project maintains its own boundary conditions without constant human prompting.
-   **Integrated Experience**: Sensory signals appear as native Gemini events, making the system feel "alive."
-   **Low Overhead**: A Python script using `inotify` or `watchdog` is extremely lightweight.

### Negative

-   **Process Management**: Background processes can sometimes become "orphaned" if the main session crashes (mitigated by PID tracking in `.ai-workspace/SENSORY_PID`).
-   **Resource Contention**: Multiple project sensors could theoretically compete for CPU on low-resource machines.

### Mitigation

-   The `aisdlc_sense` tool will include a **stop/restart** mechanism.
-   The watcher script will have a configurable "Cooldown" period to avoid infinite loops of sensing and signal generation.
-   Thresholds for sensors (e.g., "how often to check for CVEs") will be configurable in `project_constraints.yml`.

---

## References

- [GEMINI_GENESIS_DESIGN.md](../GEMINI_GENESIS_DESIGN.md) §2.3
- [AISDLC_V2_DESIGN.md](../../claude_aisdlc/AISDLC_V2_DESIGN.md) §1.8 (Sensory Service)
