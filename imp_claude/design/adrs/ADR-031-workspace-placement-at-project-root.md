# ADR-031: Workspace Must Be Placed at Project Root

**Status**: Accepted
**Date**: 2026-03-08
**Implements**: REQ-TOOL-015
**Deciders**: Jim Morley

---

## Context

The genesis installer (`gen-setup.py`) places `.ai-workspace/` in the directory from which it is invoked (CWD). There is no guard preventing it from being run inside an `imp_*/` tenant directory. When this happens, the workspace is incorrectly scoped:

```
my_project/
├── specification/              ← invisible to the monitor
├── imp_fastapi/
│   └── .ai-workspace/          ← WRONG: tenant-scoped, not project-scoped
└── imp_gemini/                 ← invisible to the monitor
```

The genesis_monitor discovers projects by finding `.ai-workspace/` and uses its parent as the project root. A tenant-scoped workspace causes:
- `specification/` to be outside the monitored boundary
- Sibling `imp_*/` tenants to be invisible
- The monitor's own dogfood view to be incorrect

This failure was observed in test06 (genesis_monitor). The workspace was at `imp_fastapi/.ai-workspace/` for the entire development sprint before being caught manually. No test existed to detect it.

---

## Decision

1. **Documentation**: The installer usage docs state explicitly: "Run from the project root (the directory containing `specification/` and `imp_*/`)."

2. **Warning**: The installer detects when CWD contains a path component matching `imp_*` and prints a warning before proceeding. It does not abort (the user may intentionally want a tenant-scoped workspace for isolated testing), but the warning is prominent.

3. **Test**: `test_install_workspace_placement.py` verifies:
   - The installer places `.ai-workspace/` in the CWD
   - A structural check: for any discovered project root, no `imp_*/` subdirectory contains a nested `.ai-workspace/`

4. **Convention**: Every project under `projects/` in this repository follows the pattern: `.ai-workspace/` at the project root alongside `specification/` and `imp_*/`.

---

## Implementation

### Installer warning (gen-setup.py)

```python
import re
from pathlib import Path

cwd = Path.cwd()
if re.search(r'/imp_[^/]+$', str(cwd)):
    print(
        "WARNING: installer is running inside an implementation tenant "
        f"({cwd.name}/). The workspace will be scoped to this directory "
        "only and will not span specification/ or sibling tenants.\n"
        "To span the full project, run the installer from the project root."
    )
```

### Structural test

```python
# test_install_workspace_placement.py
# Validates: REQ-TOOL-015

def test_no_workspace_inside_imp_tenant(tmp_path):
    """REQ-TOOL-015 AC-3: no imp_*/ dir should contain .ai-workspace/."""
    (tmp_path / "specification").mkdir()
    (tmp_path / "imp_fastapi" / ".ai-workspace").mkdir(parents=True)  # wrong

    violations = [
        d for d in tmp_path.glob("imp_*/.ai-workspace")
        if d.is_dir()
    ]
    assert violations == [], (
        f"Found .ai-workspace inside imp_* tenant(s): {violations}\n"
        "Workspace must be at the project root, not inside an implementation tenant."
    )
```

---

## Consequences

- New projects cannot accidentally create a tenant-scoped workspace without a visible warning.
- The test catches regressions automatically — if a developer runs the installer from inside `imp_*/`, the structural test fails in CI.
- The genesis_monitor test suite gains `TestWorkspacePlacement` in `test_nfr_dog.py` as the local enforcement of AC-3.
