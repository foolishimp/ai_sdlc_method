# ADR-008: Read-Only Invariant — Test-Enforced, Not Runtime-Guarded

**Status**: Accepted | **Date**: 2026-03-12
**Implements**: REQ-NFR-ARCH-002

## Decision

The read-only constraint (backend never writes) is enforced by test assertion, not
by a runtime filesystem guard (e.g., mounting read-only, wrapping `open()`).

## Rationale

- A runtime guard (monkey-patching `open()`) creates maintenance burden and false confidence
- The constraint is a code correctness property — verified by code review + tests
- The test approach: `conftest.py` captures any filesystem writes during a test run and asserts zero writes occurred after any API handler call
- This is the same pattern used in `imp_claude` (test_runtime_commands.py: "zero filesystem writes")

## Test fixture pattern

```python
@pytest.fixture
def assert_no_writes(tmp_path, monkeypatch):
    writes = []
    original_open = builtins.open
    def patched_open(file, mode='r', *args, **kwargs):
        if 'w' in mode or 'a' in mode:
            writes.append(str(file))
        return original_open(file, mode, *args, **kwargs)
    monkeypatch.setattr(builtins, 'open', patched_open)
    yield
    assert writes == [], f"API handler wrote to filesystem: {writes}"
```

## Consequences

- Every router test must use the `assert_no_writes` fixture
- The acceptance criterion "Backend handler tests confirm zero filesystem writes" (from REQ-F-GNAV-001) is automatically enforced
- Code review checklist item: "no `open(..., 'w')` in routers/ or analyzers/"
