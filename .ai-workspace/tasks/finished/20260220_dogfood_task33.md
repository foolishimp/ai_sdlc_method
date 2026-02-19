# Task #33: Dogfood AI SDLC v2.1 on Real Project — Findings

**Date**: 2026-02-20
**Status**: Complete
**Test Project**: `~/src/apps/aisdlc-dogfood/` (Python CLI bookmark manager)

---

## Summary

Traversed 3 edges (intent→requirements, requirements→design, design→code) following the command markdown and iterate agent instructions literally. The methodology fundamentally works — the LLM-as-runtime approach is viable. Six bugs/gaps found, all fixable.

## Edges Traversed

| Edge | Iterations | Result |
|------|-----------|--------|
| intent → requirements | 1 | Converged (7/7 agent + 2/2 human) |
| requirements → design | 1 | Converged (6/6 agent + 1/1 human) |
| design → code | 2 | Converged on iter 2 (3 lint fixes) |

## What Worked

1. **LLM-as-runtime is viable** — no custom code needed. The agent markdown + edge configs + project constraints provide enough structure for the LLM to follow the methodology.
2. **Checklist composition** — the layered approach (edge defaults + project constraints + feature overrides) is clear and works. $variable resolution from project_constraints.yml was straightforward.
3. **Feature vector tracking** — the trajectory section accurately recorded the path through the graph.
4. **REQ key discipline** — the template in intent_requirements.yml produced consistent REQ-{TYPE}-{DOMAIN}-{SEQ} keys. Traceability matrix in design doc was natural to produce.
5. **Iteration reports** — the structured checklist table format is useful for showing exactly what passed/failed.
6. **ADR generation** — the ADR template and guidance produced a real decision record with alternatives and consequences.

## What Broke (Bugs Found)

### BUG-1: Misnumbered Steps in aisdlc-init.md (Cosmetic)

**File**: `v2/commands/aisdlc-init.md:98-128`
**Issue**: Two steps are both numbered "Step 5" — Feature Vector Template (line 97-99) and Feature Index (line 115-128). Steps go: 1, 2, 3, 4, 5, 5, 7, 8, 9, 10.
**Impact**: Low — confusing but followable.
**Fix**: Renumber Step 5 (Feature Index) to Step 6, and shift subsequent steps.

### BUG-2: Directory Name Inconsistency in aisdlc-init.md

**File**: `v2/commands/aisdlc-init.md:53-56`
**Issue**: Step 2 directory structure shows `docs/requirements/` but Step 8 (Intent Placeholder) creates `docs/specification/INTENT.md`. The CLAUDE.md and spec documents all use `docs/specification/`. The `docs/requirements/` path is a v1.x holdover.
**Impact**: Medium — an implementor following the init command would create the wrong directory.
**Fix**: Change `docs/requirements/` to `docs/specification/` in Step 2.

### BUG-3: Feature Vector Create-If-Absent Not Specified

**File**: `v2/commands/aisdlc-iterate.md:33` and `v2/agents/aisdlc-iterate.md:61`
**Issue**: Both the command and agent say to "Load the feature vector" but don't specify what to do if it doesn't exist yet. On the first iteration for a new feature, no feature vector file exists.
**Impact**: High — blocks the first iteration for any new feature.
**Fix**: Add a step: "If the feature vector file does not exist, create it from `.ai-workspace/features/feature_vector_template.yml`, populate the feature ID, title, and intent fields, and save to `.ai-workspace/features/active/{feature}.yml`."

### BUG-4: `no_ambiguous_language` Self-Contradictory Criterion

**File**: `v2/config/edge_params/intent_requirements.yml:67-69`
**Issue**: Criterion says `No use of: "should", "may", "might"...` in the first sentence, then says `"may" only for optional` in the second sentence. These contradict — "may" is both banned and allowed.
**Impact**: Medium — confusing agent evaluation. The agent must decide which sentence to follow.
**Fix**: Remove "may" from the banned list. Rewrite as: `Requirements must not use: "should", "might", "could", "appropriate", "reasonable". Use "must" or "shall" for mandatory behaviour, "may" for optional behaviour.`

### BUG-5: `$architecture.*` Variable Prefix Undefined

**File**: `v2/config/edge_params/requirements_design.yml:72-74` and `v2/agents/aisdlc-iterate.md:71`
**Issue**: The `dependencies_sound` check references `$architecture.dependency_rules` and `$architecture.forbidden`, but the variable resolution rules in both the agent and evaluator_defaults.yml only define `$tools.*`, `$thresholds.*`, and `$standards.*`. The `$architecture.*` prefix is not listed.
**Impact**: Medium — unresolved variables. The agent must guess the resolution or skip the check.
**Fix**: Add `$architecture.{key} → architecture.{key}` to the resolution rules in both `evaluator_defaults.yml:80-83` and `aisdlc-iterate.md:71`.

### BUG-6: `compiles_or_parses` and `lint_passes` Are Duplicate Checks

**File**: `v2/config/edge_params/design_code.yml:38-51`
**Issue**: Both checks resolve to `$tools.linter.command $tools.linter.args` with `$tools.linter.pass_criterion`. For our project: `ruff check .` with "exit code 0". They are identical.
**Impact**: Low — no functional problem, just redundant.
**Fix**: Split `compiles_or_parses` into a separate syntax-only check. For Python: `command: "python -m py_compile {files}"` or `command: "$tools.syntax_checker.command"`. Alternatively, add a `syntax_checker` tool to the project_constraints template.

## What's Missing

1. **Context hash recording** — the iterate agent says to "record the context hash at each iteration" (REQ-INTENT-004), but there's no mechanism to compute it. The context_manifest.yml has a placeholder `aggregate_hash: "pending"`. Need a concrete algorithm (e.g., hash all files in `.ai-workspace/context/`).

2. **Feature index update** — the feature_index.yml is never updated during iteration. The iterate command/agent don't mention updating it. Should be updated when a feature vector is created or converges.

3. **Iteration history in feature vector** — the feature vector template has comments showing `evaluator_results` but no structured iteration log. When multiple iterations occur (like our code edge with 2 iterations), only the final state is recorded. Earlier iteration feedback is lost.

4. **No `.gitignore` scaffolded** — init doesn't create a `.gitignore` for the `.ai-workspace/snapshots/` directory or common build artifacts. The dogfood project accidentally committed `.pyc` files.

## Recommended Fixes (Prioritised)

| Priority | Bug | Impact | Effort |
|----------|-----|--------|--------|
| P1 | BUG-3: Feature vector create-if-absent | Blocks first iteration | Small — add 3 lines to command + agent |
| P1 | BUG-5: $architecture.* prefix | Unresolved variables | Small — add 1 line to resolution rules |
| P2 | BUG-4: no_ambiguous_language | Contradictory criterion | Small — rewrite 2 lines |
| P2 | BUG-2: docs/requirements/ path | Wrong directory created | Small — change 1 line |
| P3 | BUG-6: Duplicate lint checks | Redundant | Medium — add syntax_checker tool |
| P3 | BUG-1: Misnumbered steps | Cosmetic | Small — renumber |

## Test Project Artifacts

```
~/src/apps/aisdlc-dogfood/
├── .ai-workspace/          # Full scaffold (all dirs + configs)
│   ├── graph/              # Topology + 9 edge configs + evaluator defaults
│   ├── context/            # project_constraints.yml, context_manifest.yml
│   ├── features/           # REQ-F-BM-001.yml (3 edges converged)
│   └── tasks/              # ACTIVE_TASKS.md
├── docs/
│   ├── specification/
│   │   ├── INTENT.md       # INT-001: CLI Bookmark Manager
│   │   └── requirements.md # 10 requirements (5F, 2NFR, 1DATA, 2BR)
│   └── design/bookmarks/
│       ├── DESIGN.md       # 3 components, traceability matrix
│       └── adrs/           # ADR-000 template, ADR-001 storage decision
├── src/bookmarks/
│   ├── models.py           # Bookmark dataclass
│   ├── store.py            # BookmarkStore — CRUD + JSON persistence
│   └── cli.py              # CLI — argparse + subcommands
└── pyproject.toml
```
