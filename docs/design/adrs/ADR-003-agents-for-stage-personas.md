# ADR-003: Agents for Stage-Specific Personas

**Status**: Accepted
**Date**: 2025-11-25
**Deciders**: Development Tools Team
**Requirements**: REQ-F-CMD-002 (Persona Management)
**Depends On**: ADR-001 (Claude Code as Platform)

---

## Context

The AI SDLC has 7 distinct stages (Requirements → Design → Tasks → Code → System Test → UAT → Runtime Feedback). Each stage requires different:
- **Mindset** (Business Analyst vs Developer vs QA Engineer)
- **Responsibilities** (Extract requirements vs Implement code vs Validate)
- **Outputs** (REQ-* keys vs Code vs BDD scenarios)
- **Quality gates** (Acceptance criteria vs Test coverage vs UAT sign-off)

We need a mechanism to give Claude stage-appropriate context and perspective.

---

## Decision

**We will use Claude Code's agent system (`.claude/agents/*.md`) to provide stage-specific personas for each SDLC stage.**

Specifically:
- **7 agents** - One per SDLC stage
- **Markdown files** - Agent definition in `.claude/agents/aisdlc-{stage}-agent.md`
- **Role-based** - Each agent has clear role, responsibilities, inputs, outputs
- **Namespace safe** - `aisdlc-` prefix prevents conflicts

---

## The 7 Agents

| Agent | Stage | Role | Purpose |
|-------|-------|------|---------|
| `aisdlc-requirements-agent.md` | 1 | Intent Store & Traceability Hub | Transform intent → REQ-* keys |
| `aisdlc-design-agent.md` | 2 | Solution Architect | Requirements → technical architecture |
| `aisdlc-tasks-agent.md` | 3 | Project Manager | Design → work breakdown |
| `aisdlc-code-agent.md` | 4 | Software Developer | TDD implementation (RED→GREEN→REFACTOR) |
| `aisdlc-system-test-agent.md` | 5 | QA Engineer | BDD integration tests (Given/When/Then) |
| `aisdlc-uat-agent.md` | 6 | Business Analyst | Business validation & sign-off |
| `aisdlc-runtime-feedback-agent.md` | 7 | DevOps/SRE | Production monitoring & feedback loop |

---

## Rationale

### Why Agents (vs Alternatives)

**1. Stage-Appropriate Thinking** ✅

Without agents:
```
You: "Create requirements for authentication"
Claude (generic): "Okay, here's some code for authentication..."
❌ Wrong stage - jumped to implementation
```

With agents:
```
You: "Create requirements for authentication"
Claude (Requirements Agent persona): "I'll extract structured requirements with unique keys...

Generated:
- REQ-F-AUTH-001: User login with email/password
  Acceptance Criteria:
  - Valid credentials → JWT token
  - Response time < 500ms
  - Security: bcrypt hashing

Should I also extract business rules (BR-*) and constraints (C-*)?"
✅ Right stage - thinking like a Business Analyst
```

**2. Role-Based Expertise**

Each agent has specialized knowledge:
- **Requirements Agent** knows: Requirement patterns, acceptance criteria, disambiguation
- **Code Agent** knows: TDD workflow, Key Principles, refactoring patterns
- **System Test Agent** knows: BDD, Given/When/Then, integration testing
- **UAT Agent** knows: Business language, sign-off procedures

**3. Quality Gate Enforcement**

Each agent enforces stage-specific gates:
```yaml
Requirements Agent:
  - All requirements have unique keys
  - All have acceptance criteria
  - Product Owner review complete

Code Agent:
  - All code has tests (TDD)
  - Coverage ≥80%
  - Key Principles validated

UAT Agent:
  - Business sign-off obtained
  - All acceptance criteria verified
  - Production readiness confirmed
```

**4. Traceability Focus**

Each agent ensures traceability:
- **Requirements Agent**: Links to intent (upstream)
- **Design Agent**: Links to requirements
- **Code Agent**: Tags code with REQ-* keys
- **System Test Agent**: Tags tests with REQ-* keys
- **Runtime Agent**: Tags telemetry with REQ-* keys

**5. Natural Conversation Flow**

```
You: "I'm in the Requirements stage, help me analyze this intent"

Claude: [Reads aisdlc-requirements-agent.md]
        [Adopts Business Analyst mindset]
        [Focuses on requirement extraction]
        "I'll transform this intent into structured requirements..."
```

Vs without agents:
```
You: "I'm in the Requirements stage, help me analyze this intent.
     Think like a Business Analyst. Extract requirements with unique keys.
     Use REQ-F-* format. Create acceptance criteria. Don't jump to code..."

Claude: [Needs full instructions every time]
```

---

## Rejected Alternatives

### Alternative 1: Single Generic Agent
**Approach**: One Claude assistant for all stages

**Why Rejected**:
- ❌ No stage-specific expertise
- ❌ User must explain role every time
- ❌ Easy to skip stages (jump to code)
- ❌ Inconsistent quality gates

**When to Reconsider**: Never (defeats purpose of 7-stage methodology)

### Alternative 2: Commands for Stage Switching
**Approach**: `/aisdlc-requirements-stage`, `/aisdlc-code-stage` commands

**Why Rejected**:
- ❌ Commands are for actions (checkpoint, finish), not persona loading
- ❌ Confuses mechanism (commands) with content (agents)
- ❌ Harder to understand architecture
- ❌ Tested in v0.1.3, removed in v0.1.4 (vestigial)

**Lesson**: Commands invoke actions. Agents provide persona. Different purposes.

### Alternative 3: Prompt Engineering Only
**Approach**: Embed stage instructions in each command

**Why Rejected**:
- ❌ Duplicates context across commands
- ❌ Hard to maintain (update 6 commands vs 1 agent)
- ❌ No dedicated stage focus
- ❌ Loses role-based thinking

### Alternative 4: Separate AI Instances
**Approach**: Run 7 different Claude instances, one per stage

**Why Rejected**:
- ❌ Expensive (7x API costs)
- ❌ No shared context between stages
- ❌ Complex orchestration
- ❌ Over-engineering for MVP

---

## Design Pattern: Agents vs Commands vs Skills

**Clear separation of concerns**:

```
AGENTS = WHO Claude is (persona/role)
  - Define mindset and responsibilities
  - Provide stage-specific context
  - Enforce quality gates
  - Load via: User mentions stage OR reads agent file

COMMANDS = WHAT user wants done (actions)
  - Trigger specific workflows
  - Execute within conversation
  - Read/write workspace files
  - Load via: /aisdlc-command-name

SKILLS = HOW to accomplish tasks (capabilities)
  - Reusable execution patterns
  - Cross-stage capabilities
  - Composable tools
  - Load via: Plugins (always available)
```

**Example**:
```
User: "I'm working on requirements stage, checkpoint my progress"

Flow:
1. Claude reads: aisdlc-requirements-agent.md (AGENT = WHO)
2. User invokes: /aisdlc-checkpoint-tasks (COMMAND = WHAT)
3. Command uses: requirement-extraction skill (SKILL = HOW)

Result: Requirements work checkpointed with proper context
```

---

## Consequences

### Positive

✅ **Stage-Appropriate Guidance**
- Claude thinks like appropriate role (BA, Dev, QA, etc.)
- Reduces stage-skipping
- Enforces methodology

✅ **Reusable Personas**
- 7 agent files used across all projects
- Installed via templates
- Consistent across teams

✅ **Quality Gates Built-In**
- Each agent enforces stage-specific gates
- Can't proceed without meeting criteria
- Automated quality enforcement

✅ **Minimal Overhead**
- 7 markdown files (~26,000 lines total)
- No code, just documentation
- Copy via installer

✅ **Expertise Capture**
- Best practices embedded in agent personas
- Accumulates team knowledge
- Transferable across projects

### Negative

⚠️ **Manual Activation**
- User must mention stage or read agent file
- Claude doesn't auto-switch stages
- Could forget to load agent

**Mitigation**:
- Documentation emphasizes agent usage
- ACTIVE_TASKS.md shows which agent to use
- Commands can remind user of current stage

⚠️ **Large Context Files**
- aisdlc-code-agent.md: ~10,775 lines
- aisdlc-requirements-agent.md: ~10,093 lines
- Could hit context limits

**Mitigation**:
- Claude has 1M token context (plenty of room)
- Can split agents if needed in future

⚠️ **No Programmatic Enforcement**
- Agents are guidance, not strict enforcement
- Claude could still do wrong-stage work if asked
- Relies on user following methodology

**Mitigation**:
- Acceptable for MVP (AI-assisted, not AI-automated)
- Quality gates are in documentation
- Future: Could add validation hooks

---

## Implementation Strategy

### Agent File Structure
```markdown
# aisdlc-{stage}-agent.md

## Role
[Stage-specific role title]

## Mission
[What this agent is responsible for]

## Inputs
[What this agent receives from previous stage]

## Outputs
[What this agent produces for next stage]

## Quality Gates
[What must be true before proceeding]

## Skills Available
[Which skills this agent typically uses]

## Example Session
[Concrete example of this agent in action]
```

### Installation
```python
# installers/setup_all.py includes agents
# Copies claude-code/project-template/.claude/agents/* → .claude/agents/
```

### Usage
```bash
# User activates by mentioning stage
You: "I'm in the Code stage, let's implement REQ-F-AUTH-001"

# Claude reads aisdlc-code-agent.md
# Adopts Developer persona
# Thinks: RED → GREEN → REFACTOR
```

---

## Traceability

**Requirements Satisfied**:
- REQ-F-CMD-002: Persona Management ✅
  - 7 agents created
  - Role-based personas for development stages
  - Support 7-stage SDLC workflow

**Design Coverage**:
- 100% of REQ-F-CMD-002 acceptance criteria met

---

## Future Evolution

**v0.2.0**: Consider auto-detection
- Parse conversation for stage indicators
- Auto-suggest agent when stage mentioned
- Keep manual override

**v1.0.0**: Consider stage transitions
- Explicit stage gates
- Can't proceed without quality gates passing
- Automated stage progression

---

**Status**: ✅ Accepted
**Implemented**: v0.1.0 (7 agents created)
**Validated**: v0.1.5 (namespace prefix added)
**Next Review**: After MVP validation with teams
