# Active Tasks

*Last Updated: 2025-11-25 13:30*

---

## Task #13: Repurpose /aisdlc-release for Framework Release Management

**Priority**: Medium
**Status**: Not Started
**Release Target**: 1.0 MVP
**Estimated Time**: 2-3 hours
**Dependencies**: None

**Requirements Traceability**:
- REQ-F-CMD-003: Release Management Command

**SDLC Stages**: 4 - Code
**Agents**: Code Agent

**Description**:
Repurpose the `/aisdlc-release` command from example project deployment (no longer applicable since examples moved to `ai_sdlc_examples` repo) to framework release management.

**Current State**:
- Command deploys framework to `examples/local_projects/` (directory no longer exists)
- Command is orphaned with no valid targets

**Target State**:
```
/aisdlc-release command:
├── Pre-release Validation
│   ├── Check for uncommitted changes
│   ├── Run tests (if any)
│   └── Validate version format
│
├── Version Management
│   ├── Display current version (from latest tag)
│   ├── Prompt for version bump type (major/minor/patch)
│   └── Update version references in codebase
│
├── Changelog Generation
│   ├── Collect commits since last tag
│   ├── Group by type (feat, fix, docs, etc.)
│   └── Generate CHANGELOG entry
│
├── Release Creation
│   ├── Create annotated git tag
│   ├── Generate release summary
│   └── Display next steps (push tag, create GH release)
│
└── Options
    ├── --dry-run (preview without changes)
    ├── --version <ver> (explicit version)
    └── --no-changelog (skip changelog)
```

**Acceptance Criteria**:
- [ ] Validates no uncommitted changes before release
- [ ] Displays current version from latest git tag
- [ ] Supports version bump: major, minor, patch
- [ ] Updates version in marketplace.json
- [ ] Generates changelog from git commits
- [ ] Creates annotated git tag with release notes
- [ ] Provides dry-run mode
- [ ] Generates release summary report

**Work Breakdown**:
1. Remove example project deployment logic
2. Add pre-release validation (git status check)
3. Add version detection (git describe --tags)
4. Add version bump logic (semver)
5. Add changelog generation (git log parsing)
6. Add tag creation (git tag -a)
7. Add release summary output
8. Add command options (--dry-run, --version)
9. Update command documentation

**Example Output**:
```
╔══════════════════════════════════════════════════════════════╗
║           AI SDLC Method Release - v0.2.0                    ║
╚══════════════════════════════════════════════════════════════╝

📦 Current Version: v0.1.4
🆕 New Version: v0.2.0 (minor bump)

✅ Pre-release Checks:
   - No uncommitted changes ✅
   - On main branch ✅

📝 Changelog (since v0.1.4):
   feat: Add release target tracking to requirements
   feat: Repurpose release command for framework releases
   fix: Update traceability matrix format
   docs: Move examples to separate repo

🏷️  Creating tag: v0.2.0
   git tag -a v0.2.0 -m "Release v0.2.0 - Release management"

📝 Next Steps:
   1. Review changes: git show v0.2.0
   2. Push tag: git push origin v0.2.0
   3. Create GitHub release (optional)
```

**Notes**:
- Examples moved to https://github.com/foolishimp/ai_sdlc_examples
- Original command logic preserved in git history
- Implements REQ-F-CMD-003

---

## Task #12: Incorporate Ecosystem E(t) Tracking and Management

**Priority**: Medium
**Status**: Not Started (Planned for v1.5)
**Release Target**: 1.5 (Beyond MVP)
**Estimated Time**: 4-6 weeks
**Dependencies**: MVP v1.0 complete
**Feature Flag**: ecosystem-tracking

**Requirements Traceability**:
- REQ-F-ECO-001: Ecosystem Constraint Vector E(t) Tracking (NEW - v1.5)
- REQ-F-ECO-002: Eco-Intent Generation (NEW - v1.5)
- REQ-F-ECO-003: ADR Integration with E(t) Context (NEW - v1.5)
- REQ-NFR-ECO-001: Ecosystem Change Detection (NEW - v1.5)

**SDLC Stages**: 1 - Requirements, 7 - Runtime Feedback
**Agents**: Requirements Agent, Runtime Feedback Agent

**Description**:
Implement comprehensive ecosystem tracking and management as described in Section 3.6 of AI_SDLC_REQUIREMENTS.md. The ecosystem E(t) represents the external operating environment - the totality of constraints, capabilities, and resources available at time t.

**Current State** (MVP 1.0):
- E(t) concept documented in requirements specification
- Manual acknowledgment of ecosystem constraints in ADRs
- No automated tracking or change detection
- No Eco-Intent generation

**Target State** (v1.5):
```
E(t) System Components:
├── Ecosystem Tracker
│   ├── runtime_platforms(t)     # Python, Node, Java versions
│   ├── cloud_providers(t)       # AWS, GCP, Azure APIs
│   ├── available_apis(t)        # OpenAI, Stripe, Auth0, etc.
│   ├── library_ecosystems(t)    # npm, PyPI, Maven registries
│   ├── compliance_reqs(t)       # GDPR, HIPAA, SOC2 changes
│   ├── cost_landscape(t)        # Pricing models, thresholds
│   └── team_capabilities(t)     # Skills, experience matrix
│
├── Change Detector
│   ├── Security scanners        # Dependabot, npm audit, Snyk
│   ├── Deprecation monitors     # AWS Trusted Advisor, GitHub
│   ├── Version trackers         # GitHub releases, changelog feeds
│   ├── Cost monitors            # Cloud cost alerts, thresholds
│   └── Compliance trackers      # Regulatory change feeds
│
├── Eco-Intent Generator
│   ├── Security vulnerabilities → INT-ECO-SEC-{n}
│   ├── Deprecation notices     → INT-ECO-DEP-{n}
│   ├── Version updates         → INT-ECO-VER-{n}
│   ├── Cost overruns           → INT-ECO-COST-{n}
│   └── Compliance changes      → INT-ECO-COMP-{n}
│
└── ADR Context Injection
    └── Auto-populate E(t) constraints in ADR templates
```

**Key Features**:

1. **Ecosystem State Capture**
   - Snapshot E(t) at project start and major milestones
   - Track changes over time: E(t₀) → E(t₁) → E(t₂)
   - Store in project context (config/ecosystem.yml)

2. **Automated Change Detection**
   - Integrate with Dependabot for dependency vulnerabilities
   - Monitor cloud provider deprecation notices
   - Track API version changes and breaking changes
   - Alert on cost threshold breaches
   - Monitor compliance requirement updates

3. **Eco-Intent Generation**
   - Automatically generate intents when E(t) changes
   - Priority based on impact (security → high, enhancement → low)
   - Feed into normal SDLC flow via Intent Manager

4. **ADR E(t) Context**
   - ADR templates pre-populated with current E(t) state
   - Decisions explicitly linked to ecosystem constraints
   - Traceability: Decision → E(t) state → Rationale

5. **Stage Integration**
   - Requirements: Check feasibility against E(t)
   - Design: ADRs acknowledge E(t) constraints
   - Tasks: Estimation considers ecosystem solutions
   - Code: Library/API contracts from E(t)
   - System Test: Environment constraints from E(t)
   - UAT: Third-party availability considerations
   - Runtime: SLA bounded by weakest E(t) dependency

**Acceptance Criteria**:
- [ ] REQ-F-ECO-001: Ecosystem state captured in config/ecosystem.yml
- [ ] REQ-F-ECO-002: Eco-Intents auto-generated from E(t) changes
- [ ] REQ-F-ECO-003: ADR templates include E(t) context section
- [ ] REQ-NFR-ECO-001: Change detection via Dependabot, npm audit, AWS TA
- [ ] Ecosystem dashboard shows current E(t) state
- [ ] Historical E(t) tracking (snapshots over time)
- [ ] Eco-Intent priority mapping (security=critical, version=low)
- [ ] Integration tests for change detection
- [ ] Documentation: E(t) tracking guide
- [ ] Example project with E(t) tracking enabled

**Work Breakdown**:
1. **Requirements Phase** (Week 1)
   - Create REQ-F-ECO-001, 002, 003
   - Create REQ-NFR-ECO-001
   - Define E(t) schema (ecosystem.yml format)
   - Define Eco-Intent format (INT-ECO-*)

2. **Design Phase** (Week 2)
   - Design Ecosystem Tracker component
   - Design Change Detector integrations
   - Design Eco-Intent Generator
   - Create ADR-006: Ecosystem Tracking Architecture
   - Update Design Agent with E(t) awareness

3. **Implementation Phase** (Weeks 3-4)
   - Implement ecosystem.yml schema and loader
   - Implement change detection (Dependabot, npm audit)
   - Implement Eco-Intent generation logic
   - Update ADR templates with E(t) section
   - Update Requirements Agent with E(t) feasibility checks

4. **Testing Phase** (Week 5)
   - Unit tests for E(t) tracking
   - Integration tests for change detection
   - End-to-end test: E(t) change → Eco-Intent → SDLC cycle
   - BDD scenarios for Eco-Intent workflow

5. **Documentation Phase** (Week 6)
   - User guide: Setting up E(t) tracking
   - Developer guide: Adding new E(t) monitors
   - Example project with E(t) tracking
   - Update ai_sdlc_method.md with implementation details

**Example Eco-Intent Flow**:
```
1. Dependabot detects: lodash 4.17.19 → CVE-2021-23337
   ↓
2. Change Detector generates: INT-ECO-SEC-001
   Intent: "Upgrade lodash to 4.17.21 (CVE-2021-23337)"
   Priority: Critical
   E(t) context: { vulnerability: CVE-2021-23337, current: 4.17.19, target: 4.17.21 }
   ↓
3. Requirements Agent creates: REQ-F-SEC-001
   "Update lodash dependency to 4.17.21 to address CVE-2021-23337"
   Release: 1.5.1 (hotfix)
   ↓
4. Normal SDLC flow: Design → Tasks → Code → Test → Deploy
   ↓
5. Runtime validates: E(t) updated, vulnerability resolved
```

**Notes**:
- E(t) tracking is conceptually complete in requirements doc (Section 3.6)
- Implementation deferred to v1.5 (beyond MVP scope)
- Builds on existing feedback loop architecture (REQ-NFR-REFINE-001)
- Complements Runtime Feedback Agent (Stage 7)
- Key differentiator: Proactive ecosystem monitoring vs reactive incident response

**Rationale**:
- ✅ Closes the loop from external ecosystem back to requirements
- ✅ Automates detection of security, deprecation, compliance changes
- ✅ Makes E(t) constraints explicit in architectural decisions
- ✅ Enables proactive maintenance (not just reactive)
- ✅ Provides "reality check" at every stage

**References**:
- docs/requirements/AI_SDLC_REQUIREMENTS.md Section 3.6 (E(t) definition)
- docs/requirements/AI_SDLC_REQUIREMENTS.md Section 10.2.2 (Eco-Intents)
- docs/requirements/AI_SDLC_REQUIREMENTS.md Section 5.2.1 (ADRs)

---

## Task #3: Complete Design Documentation for Command System

**Priority**: Medium
**Status**: Not Started (NEEDS UPDATE - outdated after MVP scope change)
**Started**: 2025-11-23
**Estimated Time**: 2 hours (reduced from 3)
**Dependencies**: None
**Feature Flag**: N/A (documentation task)

**Requirements Traceability**:
- REQ-F-CMD-001: Slash commands for workflow
- REQ-F-CMD-002: Persona management (formerly CMD-003)

**Description**:
Create design documentation (docs/design/COMMAND_SYSTEM.md) covering:
- Command structure (.claude/commands/*.md)
- 6 implemented commands (final after persona cleanup)
- Command format and Claude Code integration
- Installer mechanism (setup_commands.py)

**Acceptance Criteria**:
- [ ] All remaining commands documented (excluding removed context switching)
- [ ] Command markdown format explained
- [ ] Traceability to requirements (updated for new numbering)
- [ ] Integration with Claude Code explained
- [ ] Examples from actual commands

**TDD Checklist**:
N/A - Documentation task

**Notes**:
- Task scope changed after Task #5 (MVP Baseline) and Task #7 (Persona cleanup)
- Context switching commands removed (5 commands)
- TODO command removed
- Persona commands removed (4 commands - vestigial)
- Final command count: 6 commands
- REQ-F-CMD-002 implemented by agents (not commands)
- Current commands: checkpoint-tasks, finish-task, commit-task, status, release, refresh-context

---

## Summary

**Total Active Tasks**: 3
- Medium Priority: 3
- Not Started: 3
  - Task #13: Repurpose /aisdlc-release for Release Management (1.0 MVP)
  - Task #3: Command System Documentation (needs scope update)
  - Task #12: Ecosystem E(t) Tracking (v1.5 - planned)

**Recently Completed**:
- ✅ Task #11: Refactor Directory Structure - Group Claude Code Assets (2025-11-25 12:00)
  - Moved plugins/ → claude-code/plugins/ (9 plugins + 4 bundles, 41 skills)
  - Moved templates/claude/ → claude-code/project-template/
  - Updated marketplace.json with new plugin paths
  - Updated 30+ documentation files with new paths
  - Updated 4 installer scripts
  - Updated all example projects
  - Created claude-code/README.md explaining structure
  - Updated claude-code/project-template/README.md
  - Preserved git history (111 files renamed using git mv)
  - Implements: REQ-F-PLUGIN-001, REQ-F-WORKSPACE-001
  - See: commit db173cd "REFACTOR: Reorganize Claude Code assets under claude-code/ directory"
- ✅ Task #9: Design Synthesis Document (2025-11-25 11:00)
  - Created AISDLC_IMPLEMENTATION_DESIGN.md (560+ lines)
  - Mapped all 17 requirements to design components
  - Referenced all 6 design docs (5,744 lines)
  - Summarized 5 ADRs
  - Created component architecture diagrams
  - Coverage: 71% implemented, 24% partial, 6% planned
  - See: `.ai-workspace/tasks/finished/20251125_1100_design_synthesis_document.md`
- ✅ Task #10: Update All Agents with Feedback Protocol (2025-11-25 03:32)
  - Added explicit feedback protocol to all 7 agents (+ 7 templates)
  - Created REQ-NFR-REFINE-001 (17th requirement)
  - Created ADR-005 (Iterative Refinement Architecture)
  - Demonstrated dogfooding (used feedback pattern to discover and fix requirement gap)
  - See: `.ai-workspace/tasks/finished/20251125_0332_update_agents_feedback_protocol.md`
- ✅ Task #6: Requirements Provenance & Completeness Validation (2025-11-25 03:24)
  - Validated 100% provenance (all 16 requirements → intent sections)
  - Confirmed 100% completeness (all MVP goals covered)
  - Passed all quality gates (unique keys, criteria, testability)
  - Corrected scope creep (MVP vs Year 1)
  - See: `.ai-workspace/tasks/finished/20251125_0324_requirements_provenance_completeness.md`
- ✅ Task #8: Rename Agents with aisdlc- Prefix (2025-11-25 03:18)
  - Renamed 21 agent files (7 main + 7 templates + 7 example)
  - Updated 30+ documentation references across 6 files
  - Achieved 100% namespace consistency (commands + agents + plugins)
  - See: `.ai-workspace/tasks/finished/20251125_0318_rename_agents_aisdlc_prefix.md`
- ✅ Task #7: Remove Vestigial Persona Commands (2025-11-25 03:15)
  - Deleted 8 persona command files (4 main + 4 templates)
  - Updated REQ-F-CMD-002 to show implemented by agents (not commands)
  - Removed persona references from documentation
  - Command count: 10 → 6 (40% reduction, 100% functional)
  - See: `.ai-workspace/tasks/finished/20251125_0310_remove_vestigial_persona_commands.md`

---

## Recovery Commands

If context is lost, run these commands to get back:
```bash
cat .ai-workspace/tasks/active/ACTIVE_TASKS.md  # This file
git status                                       # Current state
git log --oneline -5                            # Recent commits
/aisdlc-status                                   # Task queue status
```
