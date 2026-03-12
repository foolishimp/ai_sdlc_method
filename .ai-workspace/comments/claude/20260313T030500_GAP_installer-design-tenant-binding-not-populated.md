# GAP: Installer leaves design tenant binding unpopulated

**Author**: claude
**Date**: 2026-03-13T03:05:00+11:00
**Observed during**: genesis_manager project setup
**For**: all

## Observation

The installer (`gen-setup.py`) generates `project_constraints.yml` with a `structure.design_tenants` section, but leaves it commented out:

```yaml
structure:
  design_tenants:
    # - name: ""               # e.g., "scala_spark", "python_django"
    #   output_dir: ""         # e.g., "imp_scala_spark/"
    #   description: ""        # e.g., "Scala 2.13 + Spark 3.5 implementation"
```

This means the engine has no `{impl}/` path to resolve when traversing the design→code edge. Code, tests, and design artifacts would be written to unknown or defaulted locations rather than the declared implementation tenant.

genesis_monitor has the same gap — its `design_tenants` section is also unpopulated despite having an `imp_fastapi/` tenant.

## The Problem

The `active_tenant` field (or equivalent) is the mechanism that binds:
- `design→code` output → `imp_{stack}/code/`
- `design→module_decomp` → `imp_{stack}/design/`
- test generation → `imp_{stack}/tests/`

Without this binding the engine either defaults to project root (violating `root_code_policy: reject`) or writes to an arbitrary path.

## Fix

Two changes needed:

### 1. Installer: ask for tenant name during progressive init

`gen-start` Step 1 (Progressive Init) already asks for project kind and language. It should also set the initial design tenant:

```
Design tenant: auto-detected "react_vite" from existing imp_react_vite/ directory
               (or: enter tenant name, e.g. "fastapi", "react_vite", "django")
```

Write the result immediately to `project_constraints.yml` `structure.design_tenants`.

### 2. Installer: detect existing `imp_*/` directories

When `gen-setup.py` runs against a project that already has an `imp_{name}/` directory, it should auto-populate `design_tenants` from what it finds rather than leaving the section blank.

## Severity

Medium — the gap is silent. The engine won't error; it will just write artifacts to the wrong place or fail to find the tenant path during code generation. This will surface as a confusing path error at the design→code edge rather than a clear configuration error.
