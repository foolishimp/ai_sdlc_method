# ADR-S-033: Genesis-Enabled Systems — Build-Time/Runtime Separation and Homeostatic Bridge

**Series**: S (specification-level — applies to all implementations)
**Status**: Accepted
**Date**: 2026-03-11
**Scope**: Architectural boundary — Genesis as construction tool vs Genesis as runtime substrate
**Depends on**: GENESIS_BOOTLOADER.md §VI (The Gradient), ADR-S-032 (IntentObserver + EDGE_RUNNER),
  ADR-S-012 (Event Stream), REQ-F-LIFE-001

---

## Context

Genesis is a methodology system — it builds software by traversing a graph of
typed assets using `iterate()`. Once construction is complete, Genesis steps
back. The built system exists, but it has no ongoing relationship with the
methodology that produced it.

This is sufficient for many systems. It is insufficient for systems where
production behaviour must remain within specification bounds over time — where
a latency breach, a coverage gap, or a dependency change should route back into
the development graph as new work, automatically, without waiting for a human
to notice and file a ticket.

Two distinct modes exist. This ADR names them, defines their boundary, and
specifies the bridge contract that makes the second mode possible.

---

## Decision

### The Two Modes

**Built with Genesis**: Genesis is external to the system being built. It
applies the methodology during construction — traverses design, code, tests,
UAT edges — and converges. When the system ships, Genesis's relationship with
it ends. The system has no homeostatic loop. It does not observe itself. It
does not generate intents.

**Genesis-enabled**: The system, once deployed, runs the same four primitives
at runtime. Its production telemetry feeds `intent_raised` events. Its own
`dispatch_monitor` watches its own event stream. Anomalies, drifts, and
threshold breaches in production become intents that route back into the
development graph — closing the loop from runtime back to spec.

The distinction is not about build quality. A system built with Genesis can be
high-quality without being Genesis-enabled. The distinction is about whether
the system can **self-maintain** against its specification at runtime.

### The Bridge Contract

The bridge between build time and runtime is the **REQ key thread** — the
unbroken chain from spec to production telemetry:

```
Spec:         REQ-F-AUTH-001 defined with tolerance: P99 latency < 200ms
Design:       Implements: REQ-F-AUTH-001
Code:         # Implements: REQ-F-AUTH-001
Tests:        # Validates: REQ-F-AUTH-001
Telemetry:    logger.info("login", req="REQ-F-AUTH-001", latency_ms=142)
                                                                ↓
                              P99 > 200ms → delta(observed, spec) > 0
                                                                ↓
                                                         intent_raised {
                                                           trigger: "P99 latency breach",
                                                           affected_features: ["REQ-F-AUTH-001"],
                                                           delta: "observed=312ms, threshold=200ms"
                                                         }
                                                                ↓
                                                   IntentObserver → EDGE_RUNNER
                                                                ↓
                                                    back into the build graph
```

Without the REQ key at the telemetry layer, the production signal cannot trace
to the spec requirement that defined the constraint. The loop is broken. The
system has monitoring — not homeostasis.

### Formal Definition

A **Genesis-enabled system** is one that satisfies all of the following at
runtime:

1. **REQ key threading**: Production telemetry carries `req=` tags for all
   instrumented paths (REQ keys thread from spec through code to runtime
   — GENESIS_BOOTLOADER.md §XIII).

2. **Constraint tolerances at runtime**: Every production constraint has a
   measurable threshold that can be evaluated at runtime. Breach produces
   a computable delta (GENESIS_BOOTLOADER.md §X).

3. **Runtime event stream**: The system maintains an append-only event stream
   at runtime. Production signals (telemetry anomalies, health check failures,
   dependency changes) are appended as structured events with causal chains.

4. **Intent generation**: When `delta(observed_state, spec) > 0`, the system
   emits `intent_raised` into its runtime event stream. Signal source
   classifications include: `runtime_telemetry`, `health_check`, `sla_breach`,
   `ecosystem_change`.

5. **Dispatch capability**: An `IntentObserver` (ADR-S-032) watches the
   runtime event stream. Unhandled `intent_raised` events are routed to the
   development graph via `EDGE_RUNNER`. The production anomaly becomes a
   tracked feature intent.

**A system that satisfies items 1–2 but not 3–5 is built with Genesis, not
Genesis-enabled.** It has traceability and quality gates at build time. It does
not have a homeostatic loop at runtime.

### LIFE-001 as the Bridge Implementation

REQ-F-LIFE-001 (Full Lifecycle Closure) is the specification for what makes a
system Genesis-enabled. Its requirements are the bridge contract:

- Telemetry tagged with REQ keys (`req="REQ-*"` as structured field) — item 1
- Constraints with tolerances (Bootloader §X) — item 2
- CI/CD as a graph edge (Code → CI/CD → Running System) — the deployment path
- Homeostasis: `delta(running_system, spec) → intent_raised` — items 3–4
- Deviation → new INT-* intent → back into the graph — item 5
- Observer agents (dev, CI/CD, ops) — the intake for items 3–5

LIFE-001 is not lifecycle infrastructure. It is the formal specification of the
bridge between construction and runtime homeostasis.

### The Gradient at Production Scale

GENESIS_BOOTLOADER.md §VI already names this:

```
| Scale      | State          | Constraints            | Delta → 0 means       |
|------------|----------------|------------------------|-----------------------|
| Production | running system | spec (SLAs, contracts) | system within bounds  |
```

ADR-S-033 makes this row operational. "System within bounds" requires:
- the constraints are defined with tolerances (Bootloader §X)
- the running system emits observable signals against those tolerances
- delta > 0 routes through the same homeostatic path as any other delta

The production row is not a special case. It is the same `iterate()` at
production scale, with the running system as the asset and the spec (SLAs,
contracts) as the constraint surface.

### Genesis as Construction OS, Genesis-Enabled as Runtime OS

Two distinct deployment modes for the same formal system:

**Genesis as construction OS** (always):
- `events.jsonl` = the build-time event stream
- `dispatch_monitor` = watches the build event stream
- `intent_raised` = signals from gap analysis, tests, spec review
- `EDGE_RUNNER` = constructs the next artifact
- Terminates when the system is shipped

**Genesis-enabled runtime OS** (for systems that choose it):
- `events.jsonl` = the production event stream
- `dispatch_monitor` = watches the production event stream
- `intent_raised` = signals from telemetry, health checks, SLA breaches
- `EDGE_RUNNER` = routes production anomalies back to the build graph
- Does not terminate — runs for the life of the system

The same four primitives. The same one operation. Different assets, different
constraints, different scale. The formal system is scale-invariant by design.

---

## Consequences

**Positive**:
- The value proposition of Genesis is two sentences: "Genesis builds software.
  A Genesis-enabled system maintains itself against its specification."
- LIFE-001's requirements are now formally motivated — not "lifecycle
  infrastructure" but "the bridge contract for homeostasis at runtime."
- The REQ key thread (`# Implements:` → `req=` in telemetry) is not optional
  metadata — it is the mechanism by which production signals trace to spec
  requirements. Without it, a system cannot be Genesis-enabled.
- The `dispatch_monitor` architecture (ADR-S-032) works identically at build
  time and runtime. The same code serves both modes.

**Negative / Trade-offs**:
- "Genesis-enabled" is a higher commitment than "built with Genesis". It
  requires LIFE-001 implementation, runtime event stream infrastructure, and
  `req=` telemetry discipline across the entire production stack.
- Not all systems need runtime homeostasis. A CLI tool, a migration script, a
  batch job — building with Genesis is sufficient. Requiring Genesis-enablement
  for all systems would be over-engineering. The distinction must be explicit
  in the feature vector (`genesis_enabled: true|false` in project_constraints).

---

## Relationship to Existing ADRs

| ADR | Relationship |
|-----|-------------|
| GENESIS_BOOTLOADER §VI | Production row — ADR-S-033 makes it operational |
| ADR-S-003 (REQ key format) | REQ key thread is the bridge mechanism |
| ADR-S-010 (Constraint tolerances) | Runtime constraints require tolerances to generate delta |
| ADR-S-012 (Event stream) | Runtime event stream is the same substrate |
| ADR-S-032 (IntentObserver) | dispatch_monitor works identically at runtime |
| REQ-F-LIFE-001 | Implementation contract for the bridge |

---

## References

- [GENESIS_BOOTLOADER.md](../core/GENESIS_BOOTLOADER.md) §VI (The Gradient — production scale row)
- [GENESIS_BOOTLOADER.md](../core/GENESIS_BOOTLOADER.md) §X (Constraint Tolerances)
- [GENESIS_BOOTLOADER.md](../core/GENESIS_BOOTLOADER.md) §XIII (Feature Vectors — REQ key thread)
- [ADR-S-032](ADR-S-032-intentobserver-edgerunner-dispatch-contract.md) — dispatch_monitor architecture
- [requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) REQ-F-LIFE-001
