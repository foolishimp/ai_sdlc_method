# Roo Code Installers (Placeholder)

Purpose
- Setup scripts for installing AISDLC framework into Roo Code projects.
- Mirrors `claude-code/installers/` behavior but targets Roo Code configuration.

## Planned Scripts

| Script | Purpose |
|--------|---------|
| `setup_workspace.py` | Copy `.ai-workspace/` and validate structure |
| `setup_modes.py` | Install Roo custom modes (`.roo/modes/` or `.roomodes`) |
| `setup_rules.py` | Install custom instructions to `.roo/rules/` |
| `setup_plugins.py` | Install/update Roo AISDLC packages |
| `setup_all.py` | Complete installation orchestrator |
| `setup_reset.py` | Clean uninstall with preservation options |
| `validate_traceability.py` | Regenerate traceability artifacts |

## Roo Code Configuration Targets

### Custom Modes
```
.roo/
└── modes/
    ├── aisdlc-requirements.json
    ├── aisdlc-design.json
    ├── aisdlc-tasks.json
    ├── aisdlc-code.json
    ├── aisdlc-system-test.json
    ├── aisdlc-uat.json
    └── aisdlc-runtime.json
```

Or single file: `.roomodes` (JSON array of mode definitions)

### Custom Instructions (Rules)
```
.roo/
└── rules/
    ├── key-principles.md
    ├── tdd-workflow.md
    ├── req-tagging.md
    └── feedback-protocol.md
```

### Memory Bank (Optional)
```
.roo/
└── memory-bank/
    ├── projectbrief.md
    ├── techstack.md
    └── activecontext.md
```

## Status

Placeholder only; align implementation with `docs/design/roo_aisdlc/` and mirror behavior of `claude-code/installers/`.
