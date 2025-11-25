# runtime-skills Plugin

**Production Feedback Loop - Close the SDLC Cycle**

Version: 1.0.0

---

## Overview

The `runtime-skills` plugin closes the feedback loop from production back to intent. Tags telemetry with REQ-* keys, sets up observability platforms, and traces production issues back to create new remediation intents.

**Completes the cycle**: Intent → ... → Runtime → Alert → New Intent ♻️

---

## Capabilities

### 1. Telemetry Tagging
**Skill**: `telemetry-tagging`
**Purpose**: Tag logs/metrics/traces with REQ-* for backward traceability

### 2. Observability Setup
**Skill**: `create-observability-config`
**Purpose**: Setup Datadog/Prometheus/Splunk with REQ-* dashboards

### 3. Production Issue Tracing
**Skill**: `trace-production-issue`
**Purpose**: Alert → REQ-* → Intent, create remediation intent

---

## The Feedback Loop

```
1. Deploy (Code tagged with REQ-*)
   ↓
2. Runtime (Telemetry tagged: req:<REQ-ID>)
   ↓
3. Monitor (Dashboard per REQ-*)
   ↓
4. Alert (SLA violation detected)
   ↓
5. Trace (Alert → REQ-* → Original Intent)
   ↓
6. Create Intent (INT-150: Fix performance issue)
   ↓
7. SDLC Begins Again ♻️
```

**Homeostatic Production**: System self-corrects via feedback

---

## Installation

```bash
/plugin install @aisdlc/runtime-skills
```

---

## Dependencies

- **Required**: `@aisdlc/aisdlc-core`

---

## Skills Status

| Skill | Lines | Status |
|-------|-------|--------|
| telemetry-tagging | 246 | ✅ |
| create-observability-config | 218 | ✅ |
| trace-production-issue | 286 | ✅ |
| **TOTAL** | **750** | **✅** |

---

**"Excellence or nothing"** 🔥
