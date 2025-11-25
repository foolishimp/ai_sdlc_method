# ADR-004: Skills for Reusable Capabilities

**Status**: Accepted
**Date**: 2025-11-25
**Deciders**: Development Tools Team
**Requirements**: REQ-F-PLUGIN-001 (Plugin System), Implicit in all stage requirements
**Depends On**: ADR-001 (Claude Code as Platform), ADR-003 (Agents for Personas)

---

## Context

Agents provide stage-specific **personas** (WHO Claude is), but agents need **capabilities** (HOW to accomplish tasks). Many capabilities are reusable across multiple stages and agents.

### The Problem

Without reusable capabilities:
```
Requirements Agent needs: requirement-extraction
Design Agent needs: requirement-extraction (to understand requirements)
UAT Agent needs: requirement-extraction (to create test cases)

Result: Duplicate logic in 3 agent files
```

With reusable capabilities:
```
Skill: requirement-extraction (defined once)
Available to: All agents
Used by: Requirements Agent, Design Agent, UAT Agent

Result: Single source of truth, reused 3x
```

---

## Decision

**We will use a skills-based architecture where reusable capabilities are packaged as skills within plugins.**

Specifically:
- **Skills** = Reusable capabilities/processes (requirement-extraction, tdd-workflow, etc.)
- **Plugin-based** = Skills delivered via plugin system
- **Cross-cutting** = Skills available to any agent (or Claude directly)
- **Categorized** = Skills grouped by domain (requirements-skills, code-skills, testing-skills)

---

## Skills Architecture

### Pattern: Skills as Reusable Tools

```
┌──────────────────────────────────────────────────────────┐
│                    AGENT LAYER                            │
│  (WHO Claude is + Stage Responsibilities)                │
├──────────────────────────────────────────────────────────┤
│  Requirements Agent  │  Code Agent   │  System Test Agent│
│  ─────────┬──────────┴──────┬───────┴─────────┬─────────│
│           │                 │                  │         │
│           │ USES            │ USES             │ USES    │
│           ▼                 ▼                  ▼         │
└───────────────────────────────────────────────────────────┘
            │                 │                  │
            ▼                 ▼                  ▼
┌──────────────────────────────────────────────────────────┐
│                    SKILLS LAYER                          │
│  (HOW to accomplish tasks)                               │
├──────────────────────────────────────────────────────────┤
│  requirement-extraction  │  tdd-workflow  │  bdd-workflow│
│  validate-requirements   │  red-phase     │  run-tests   │
│  create-traceability     │  green-phase   │  coverage    │
│  disambiguate            │  refactor      │  scenarios   │
└──────────────────────────────────────────────────────────┘
```

**Key Insight**: Multiple agents can use the same skill

---

## Rationale

### Why Skills (vs Alternatives)

**1. Reusability** ✅

Single skill, multiple uses:
```
Skill: requirement-extraction

Used by:
- Requirements Agent: Extract REQ-* from intent
- Design Agent: Understand requirements being designed
- Code Agent: Understand requirements being implemented
- System Test Agent: Understand requirements being tested
- Runtime Agent: Link production issues to requirements

Result: 1 skill definition → 5 agent uses
```

**2. Composability** ✅

Skills combine for complex workflows:
```yaml
tdd-workflow skill:
  uses:
    - red-phase skill
    - green-phase skill
    - refactor-phase skill
    - commit-with-req-tag skill

  result: Complete TDD cycle from one invocation
```

**3. Cross-Stage Availability**

Some skills apply to ALL stages:
```
Foundation skills (available everywhere):
- requirement-traceability
- check-requirement-coverage
- propagate-req-keys
- apply-key-principles

Used by: Any agent, any stage
```

**4. Homeostatic Pairs** ✅

Skills implement sensor/actuator pattern:
```
Sensor Skills (detect):
- check-requirement-coverage (find requirements without design/code/tests)
- validate-test-coverage (find code without tests)
- detect-unused-code (find dead code)

Actuator Skills (fix):
- propagate-req-keys (tag code with REQ-*)
- generate-missing-tests (create tests)
- prune-unused-code (remove dead code)

Result: Self-correcting system
```

**5. Plugin Distribution**

Skills packaged by domain:
```
claude-code/plugins/
├── requirements-skills/     # 8 skills for requirements work
├── design-skills/           # 3 skills for architecture
├── code-skills/             # 21 skills for TDD/BDD/generation
├── testing-skills/          # 4 skills for coverage/validation
└── runtime-skills/          # 3 skills for observability
```

Users install only what they need.

---

## Rejected Alternatives

### Alternative 1: Embed Logic in Agents
**Approach**: Put all capability logic directly in agent files

**Why Rejected**:
- ❌ Massive duplication (requirement-extraction in 5 agents)
- ❌ Hard to maintain (update 5 places for 1 change)
- ❌ Can't reuse across agents
- ❌ Agent files become huge (20,000+ lines)

### Alternative 2: External Tool Scripts
**Approach**: Python scripts for capabilities (`extract_requirements.py`)

**Why Rejected**:
- ❌ Context-switching (leave Claude, run script, return)
- ❌ Claude can't invoke programmatically
- ❌ Requires Python runtime
- ❌ Not conversational

**Note**: We DO have Python tools (validate_traceability.py) but for automation, not interactive AI work

### Alternative 3: Prompt Templates Only
**Approach**: Just give Claude prompts like "extract requirements"

**Why Rejected**:
- ❌ No structured reuse
- ❌ Inconsistent execution
- ❌ No versioning
- ❌ Hard to compose
- ❌ Doesn't scale (41 skills × ad-hoc prompts = chaos)

### Alternative 4: Code Libraries
**Approach**: Python/JS libraries agents call programmatically

**Why Rejected**:
- ❌ Requires code execution (not MVP scope)
- ❌ Language-specific
- ❌ Adds complexity
- ❌ Claude Code doesn't execute arbitrary code

**When to Reconsider**: If programmatic execution needed (advanced features)

---

## Skills Taxonomy

### By Type (Pattern)

**Sensors** (detect quality gaps):
- `check-requirement-coverage`
- `validate-test-coverage`
- `detect-unused-code`
- `detect-complexity`

**Actuators** (fix quality gaps):
- `propagate-req-keys`
- `generate-missing-tests`
- `prune-unused-code`
- `simplify-complex-code`

**Orchestrators** (multi-step workflows):
- `tdd-workflow` (RED → GREEN → REFACTOR)
- `bdd-workflow` (Given/When/Then)

**Generators** (create artifacts):
- `autogenerate-from-business-rules`
- `autogenerate-validators`
- `autogenerate-formulas`

**Validators** (check correctness):
- `validate-requirements`
- `validate-design-coverage`
- `validate-test-coverage`

**Extractors** (parse/transform):
- `requirement-extraction`
- `extract-business-rules`
- `extract-constraints`
- `extract-formulas`

### By Stage (When Used)

**Requirements Stage** (9 skills):
- requirement-extraction, disambiguate-requirements
- extract-business-rules, extract-constraints, extract-formulas
- validate-requirements, refine-requirements
- create-traceability-matrix, requirement-traceability

**Design Stage** (3 skills):
- design-with-traceability
- create-adrs
- validate-design-coverage

**Code Stage** (21 skills):
- TDD: tdd-workflow, red-phase, green-phase, refactor-phase, commit-with-req-tag
- BDD: bdd-workflow, write-scenario, implement-step-definitions
- Generation: autogenerate-from-business-rules, autogenerate-validators
- Tech Debt: detect-unused-code, prune-unused-code
- Principles: apply-key-principles, seven-questions-checklist

**System Test Stage** (4 skills):
- run-integration-tests
- validate-test-coverage
- generate-missing-tests
- create-coverage-report

**Runtime Feedback Stage** (3 skills):
- telemetry-tagging
- create-observability-config
- trace-production-issue

**Cross-Stage** (Foundation skills available everywhere):
- requirement-traceability
- check-requirement-coverage
- propagate-req-keys

---

## Implementation

### Skill Definition Format

```markdown
# Skill: requirement-extraction

## Purpose
Extract structured requirements (REQ-F-*, REQ-NFR-*, REQ-DATA-*) from raw intent.

## Inputs
- Raw intent (INTENT.md or user statement)

## Outputs
- Structured requirements with unique keys
- Acceptance criteria for each
- Traceability to intent

## Process
1. Read intent document
2. Identify functional vs non-functional needs
3. Generate unique REQ-* keys
4. Write acceptance criteria
5. Create traceability links

## Example
Input: "Users need to log in"
Output: REQ-F-AUTH-001: User login with email/password
        Acceptance: Valid credentials → JWT token
```

### Plugin Packaging
```
claude-code/plugins/requirements-skills/
├── .claude-plugin/
│   └── plugin.json           # Metadata
├── skills/
│   ├── requirement-extraction/
│   │   └── SKILL.md          # Skill definition
│   ├── disambiguate-requirements/
│   │   └── SKILL.md
│   └── ...
└── README.md                 # Plugin overview
```

### Agent Integration
```markdown
# In aisdlc-requirements-agent.md

## Skills You Use

From requirements-skills plugin:
- requirement-extraction
- disambiguate-requirements
- extract-business-rules
- validate-requirements
- create-traceability-matrix

From aisdlc-core plugin:
- requirement-traceability
- check-requirement-coverage
- propagate-req-keys
```

---

## Consequences

### Positive

✅ **DRY Principle**
- Define once, use many times
- Update once, affects all agents

✅ **Composability**
- Skills combine for complex workflows
- Orchestrator skills (tdd-workflow) compose atomic skills (red-phase, green-phase)

✅ **Plugin Distribution**
- Skills grouped by domain
- Install only what you need
- Corporate can create custom skills

✅ **Homeostatic Architecture**
- Sensor/actuator pairs enable self-correction
- Quality maintained automatically
- Gaps detected and fixed

✅ **Documentation as Code**
- Skills are documented in markdown
- Examples included
- Self-explanatory

### Negative

⚠️ **41 Skills to Learn**
- Large surface area
- Could be overwhelming

**Mitigation**:
- Skills organized by plugin
- Most users only need 1-2 plugins
- Bundles curate common sets
- Documentation provides quick reference

⚠️ **No Skill Execution Environment**
- Skills are documentation, not executable code
- Claude interprets and executes
- No programmatic guarantees

**Mitigation**:
- Acceptable for AI-assisted workflows
- Clear skill definitions minimize variance
- Future: Could add validation/testing

⚠️ **Skill Discovery**
- How does user find available skills?
- No `/skills list` command

**Mitigation**:
- SKILLS_INVENTORY.md provides catalog
- Plugin READMEs list skills
- Can add discovery command in future

---

## Metrics

- **Total Skills**: 41 across 7 plugins
- **Average Skill Complexity**: ~50 lines documentation
- **Total Skill Docs**: ~2,000 lines
- **Reuse Factor**: Average skill used by 2.3 agents
- **Maintenance**: Update 1 skill → affects multiple agents

---

## Validation

**Does this satisfy requirements?**

All requirements implicitly rely on skills:
- REQ-F-CMD-002: Agents USE skills to perform their roles ✅
- REQ-F-PLUGIN-001: Skills distributed via plugins ✅
- REQ-NFR-TRACE-001: Traceability skills enable requirement tracking ✅
- REQ-F-TESTING-001: Testing skills validate coverage ✅

**Architecture alignment**:
- ✅ Agents = WHO (persona)
- ✅ Commands = WHAT (action)
- ✅ Skills = HOW (capability)

Clear separation of concerns.

---

## Related Decisions

- **ADR-001**: Claude Code as Platform (skills delivered via plugins)
- **ADR-002**: Commands for Workflow (commands invoke skills)
- **ADR-003**: Agents for Personas (agents use skills)

---

## Example: How Agents, Commands, and Skills Work Together

```
User: "I'm in Code stage, checkpoint my TDD progress"

1. AGENT: aisdlc-code-agent.md loads
   → Claude thinks like a Developer
   → Knows TDD workflow (RED → GREEN → REFACTOR)
   → Enforces test coverage ≥80%

2. COMMAND: /aisdlc-checkpoint-tasks invoked
   → Analyzes conversation for completed work
   → Updates task status
   → Creates finished task docs

3. SKILLS used by command:
   → check-requirement-coverage (scan for REQ-* tags)
   → validate-test-coverage (check if tests written)
   → propagate-req-keys (ensure code tagged)
   → create-coverage-report (generate metrics)

Result:
- Agent provides Developer mindset
- Command triggers checkpoint action
- Skills execute the actual work
```

**Three layers working together**: Agent (WHO) + Command (WHAT) + Skills (HOW) = Complete workflow

---

## Future Evolution

**v0.2.0**: Skill Chaining
- Skills can declare dependencies on other skills
- Automatic sub-skill invocation
- DAG-based execution

**v1.0.0**: Skill Validation
- Test skills to ensure correctness
- Validate skill outputs
- Measure skill effectiveness

---

**Status**: ✅ Accepted
**Implemented**: v0.1.0 (41 skills across 7 plugins)
**Next Review**: After MVP validation
