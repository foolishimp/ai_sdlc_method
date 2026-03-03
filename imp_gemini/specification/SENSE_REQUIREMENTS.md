# Requirements: Sensory Systems (REQ-F-SENSE-001)

**Implements**: REQ-SENSE-001, REQ-SENSE-002, REQ-SENSE-003, REQ-SENSE-004, REQ-SENSE-005, REQ-SENSE-006

## 1. Interoceptive Monitoring (REQ-SENSE-001)
The system must observe its own internal state (events, feature vectors, task queue) and generate signals when deviations occur.

## 2. Exteroceptive Monitoring (REQ-SENSE-002)
The system must observe external environment state (filesystem, git, upstream APIs) and generate signals when relevant changes occur.

## 3. Sensory Service (REQ-SENSE-003)
Monitoring must run as a continuous background service, not just on-demand.

## 4. Signal Triage (REQ-SENSE-004)
Signals from sensors must be classified by ambiguity and severity.

## 5. Artifact Write Observation (REQ-SENSE-005)
Specifically detect when new assets are written to the filesystem and trigger the reflex protocol.

## 6. Telemetry Integration (REQ-SENSE-006)
Sensory data must be emitted as OpenLineage events to the shared event stream.
