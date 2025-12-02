# Consolidated Skills

This directory contains **11 consolidated skill documents** that replace the original **42 granular skills**.

## Consolidation Mapping

| Consolidated Skill | Original Skills (42) | Stage |
|-------------------|---------------------|-------|
| **tdd-complete-workflow.md** | tdd-workflow, red-phase, green-phase, refactor-phase, commit-with-req-tag | Code |
| **bdd-complete-workflow.md** | bdd-workflow, write-scenario, implement-step-definitions, implement-feature, refactor-bdd | System Test/UAT |
| **requirements-extraction.md** | requirement-extraction, disambiguate-requirements, refine-requirements, extract-business-rules, extract-constraints, extract-formulas | Requirements |
| **requirements-validation.md** | validate-requirements, create-traceability-matrix | Requirements |
| **design-with-traceability.md** | create-adrs, design-with-traceability, validate-design-coverage | Design |
| **code-generation.md** | autogenerate-constraints, autogenerate-formulas, autogenerate-from-business-rules, autogenerate-validators | Code |
| **technical-debt-management.md** | detect-complexity, detect-unused-code, prune-unused-code, simplify-complex-code | Code |
| **test-coverage-management.md** | create-test-specification, generate-missing-tests, validate-test-coverage, run-integration-tests, create-coverage-report | System Test |
| **runtime-observability.md** | create-observability-config, telemetry-tagging, trace-production-issue | Runtime |
| **traceability-core.md** | check-requirement-coverage, propagate-req-keys, requirement-traceability | All Stages |
| **key-principles.md** | apply-key-principles, seven-questions-checklist | Code |

## Why Consolidate?

### Before: 42 Granular Skills
- Many skills were sub-steps of larger workflows
- Users had to understand skill relationships
- Context switching between related skills
- Redundant content across skills

### After: 11 Comprehensive Workflows
- Each skill is a complete, self-contained workflow
- Clear mapping to SDLC stages
- All steps in one document
- Easier to understand and use

## Skills by SDLC Stage

```
Requirements Stage:
  - requirements-extraction.md    (extract + disambiguate)
  - requirements-validation.md    (validate + matrix)

Design Stage:
  - design-with-traceability.md   (ADRs + components + APIs)

Tasks Stage:
  (Use requirements-extraction for work breakdown)

Code Stage:
  - tdd-complete-workflow.md      (RED→GREEN→REFACTOR)
  - code-generation.md            (from BR-*/C-*/F-*)
  - technical-debt-management.md  (detect + eliminate)
  - key-principles.md             (7 principles)

System Test Stage:
  - bdd-complete-workflow.md      (Given/When/Then)
  - test-coverage-management.md   (coverage + gaps)

UAT Stage:
  - bdd-complete-workflow.md      (business validation)

Runtime Feedback Stage:
  - runtime-observability.md      (telemetry + deviation)

All Stages:
  - traceability-core.md          (REQ-* propagation)
```

## Usage

Each consolidated skill includes:
1. **When to Use** - Clear guidance on applicability
2. **Complete Workflow** - All phases in one document
3. **Templates** - Ready-to-use code/document templates
4. **Output Format** - Expected output after completion
5. **Configuration** - Plugin configuration options
6. **Homeostasis Behavior** - Self-healing patterns

## Migration from Granular Skills

If you were using the granular skills:

| Old Invocation | New Invocation |
|----------------|----------------|
| `red-phase` then `green-phase` | `tdd-complete-workflow` |
| `write-scenario` then `implement-step-definitions` | `bdd-complete-workflow` |
| `requirement-extraction` then `disambiguate-requirements` | `requirements-extraction` |
| `detect-unused-code` then `prune-unused-code` | `technical-debt-management` |

## Original Skills Location

The original 42 granular skills remain in `../skills/` for reference and backward compatibility.

---

**"Excellence or nothing"**
