# Basis Projection: Sensory Systems (REQ-F-SENSE-001)

**Implements**: REQ-SENSE-001, REQ-SENSE-002, REQ-SENSE-003, REQ-SENSE-004, REQ-SENSE-005, REQ-SENSE-006

## 1. `gemini_cli/engine/sensory.py`
Define `SensoryService`, `Sensor` (Base), `Signal`, `Ambiguity`, and `Severity`.

## 2. `gemini_cli/engine/sensors.py`
Implement `FilesystemSensor` using `os.stat` (to avoid external dependencies for now) and `EventSensor`.

## 3. `gemini_cli/cli.py`
Implement `gemini sense` command.

## 4. `tests/test_sensory.py`
Verify that writing a file triggers a signal and that the background service correctly classifies signals.
