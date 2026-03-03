# Module Decomposition: Sensory Systems (REQ-F-SENSE-001)

**Implements**: REQ-SENSE-001, REQ-SENSE-002, REQ-SENSE-003, REQ-SENSE-004, REQ-SENSE-005, REQ-SENSE-006

## New Modules
- **`gemini_cli.engine.sensory`**: Core sensory service and signal types.
- **`gemini_cli.engine.sensors`**: Concrete sensor implementations (Filesystem, Event, Feature).

## Impacted Modules
- **`gemini_cli.cli`**: Add a `sense` command to start the background service.
- **`gemini_cli.engine.iterate`**: Integrate with sensory signals for protocol verification.
