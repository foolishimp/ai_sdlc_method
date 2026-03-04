import sys
from pathlib import Path

# Add imp_gemini to sys.path
sys.path.append(str(Path.cwd() / "imp_gemini"))

from gemini_cli.engine.state import EventStore

def main():
    workspace_root = Path.cwd() / "imp_gemini" / ".ai-workspace"
    store = EventStore(workspace_root)
    
    event = store.emit(
        event_type="test_event",
        project="imp_gemini",
        feature="REQ-F-TRACING-001",
        edge="code\u2194unit_tests",
        delta=1,
        data={"message": "Phoenix/OTLP integration test", "regime": "deterministic"}
    )
    print(f"  [TEST] Emitted event: {event.get('run', {}).get('runId')}")

if __name__ == "__main__":
    main()
