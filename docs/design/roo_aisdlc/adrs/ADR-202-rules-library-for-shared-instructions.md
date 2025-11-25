# ADR-202: Rules Library for Shared Instructions

## Status

Accepted

## Context

Multiple AISDLC modes need to share common instructions:
- Key Principles (all modes, especially Code)
- TDD Workflow (Code mode)
- BDD Workflow (System Test, UAT modes)
- REQ Tagging (all modes)
- Feedback Protocol (all modes)
- Workspace Safeguards (all modes)

In Claude Code, these are embedded in agent markdown files or referenced from plugin docs. Roo Code provides **Custom Instructions** that can be stored as files and loaded via `@rules/<filename>` syntax.

### Requirements Addressed

- REQ-F-TESTING-001: Coverage Integration
- REQ-F-TESTING-002: Test Generation
- REQ-NFR-TRACE-001: Traceability Matrix
- REQ-NFR-TRACE-002: Requirement Key Propagation
- REQ-NFR-REFINE-001: Iterative Refinement

### Options Considered

1. **Inline in modes**: Embed all instructions in each mode's customInstructions
2. **External rules files**: Store in `.roo/rules/` and reference via @rules/
3. **Memory bank**: Store as memory bank files that auto-load

## Decision

Use **Option 2: External rules files** stored in `.roo/rules/`.

```
.roo/
└── rules/
    ├── key-principles.md
    ├── tdd-workflow.md
    ├── bdd-workflow.md
    ├── req-tagging.md
    ├── feedback-protocol.md
    └── workspace-safeguards.md
```

### Rule Loading in Modes

```json
{
  "customInstructions": "@rules/key-principles.md\n@rules/tdd-workflow.md\n@rules/req-tagging.md"
}
```

### Rule File Contents

| File | Content | ~Lines |
|------|---------|--------|
| `key-principles.md` | 7 Key Principles with explanations | 100 |
| `tdd-workflow.md` | RED-GREEN-REFACTOR-COMMIT cycle | 80 |
| `bdd-workflow.md` | Given/When/Then templates and patterns | 60 |
| `req-tagging.md` | REQ-* format, tagging rules, validation | 50 |
| `feedback-protocol.md` | Upstream/downstream communication | 70 |
| `workspace-safeguards.md` | Validation, safety, no destructive writes | 40 |

## Consequences

### Positive

- **DRY**: Rules defined once, used by multiple modes
- **Maintainability**: Update rule in one place, all modes get it
- **Transparency**: Rules are visible files users can read and customize
- **Parity**: Maps to Claude's plugin docs structure
- **Versioning**: Rules can be versioned independently

### Negative

- **Loading overhead**: Multiple files loaded per mode switch
- **Dependency**: Modes depend on rules files existing
- **Customization risk**: User modifications might break modes

### Mitigations

- Installer validates all rule files are present
- Rule files are marked with version comments
- Documentation warns about modification impacts

## References

- REQ-F-TESTING-001: Coverage Integration
- REQ-NFR-TRACE-001: Traceability Matrix
- Claude plugin docs: `claude-code/plugins/aisdlc-methodology/docs/`
