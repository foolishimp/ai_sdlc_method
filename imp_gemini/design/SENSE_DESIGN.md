# Design: Sensory Systems (REQ-F-SENSE-001)

**Implements**: REQ-SENSE-001, REQ-SENSE-002, REQ-SENSE-003, REQ-SENSE-004, REQ-SENSE-005, REQ-SENSE-006

## 1. Architecture
A `SensoryService` class will orchestrate multiple `Sensor` implementations. Each sensor runs in a thread or as a periodic poll.

## 2. Signal Model
```python
@dataclass
class Signal:
    source: str
    ambiguity: Ambiguity # zero, bounded, unbounded
    severity: Severity # informational, warning, critical
    payload: Dict[str, Any]
```

## 3. Sensors
- **`EventSensor`**: Polls `events.jsonl` for anomalies or specific patterns.
- **`FilesystemSensor`**: Uses `watchdog` (if available) or periodic `stat` to detect asset writes.
- **`FeatureSensor`**: Monitors `features/active/*.yml` for stale vectors.

## 4. Reflex Integration
When a `FilesystemSensor` detects a write, it immediately calls the `IterateEngine` to verify the protocol (Reflex Phase).
