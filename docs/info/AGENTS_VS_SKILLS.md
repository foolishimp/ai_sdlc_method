# Agents vs Skills - Architecture Explained

**Last Updated:** 2025-11-23
**Purpose:** Clarify the relationship between agents (personas) and skills (capabilities)

---

## 🎭 Agents = Personas/Roles (WHO)

**Definition:** Agents are **role-based personas** for specific SDLC stages. They define WHO is working and WHAT their goals are.

**Location:** `templates/claude/.claude/agents/` (7 agents)

**The 7 Stage Agents:**

1. **requirements-agent.md** - Requirements Stage
   - Role: Business Analyst / Requirements Engineer
   - Goal: Transform intent → structured REQ-* requirements
   - Mindset: Thorough, detail-oriented, business-focused

2. **design-agent.md** - Design Stage
   - Role: Solution Architect / Technical Designer
   - Goal: Transform requirements → technical architecture
   - Mindset: Systematic, acknowledges ecosystem E(t)

3. **tasks-agent.md** - Tasks Stage
   - Role: Project Manager / Scrum Master
   - Goal: Break design → work units (Jira tickets)
   - Mindset: Organized, dependency-aware, capacity-focused

4. **code-agent.md** - Code Stage
   - Role: Software Developer / Engineer
   - Goal: Implement features using TDD
   - Mindset: Test-first, quality-obsessed, follows Key Principles

5. **system-test-agent.md** - System Test Stage
   - Role: QA Engineer / Test Automation Engineer
   - Goal: Create BDD integration tests
   - Mindset: Validation-focused, Given/When/Then thinking

6. **uat-agent.md** - UAT Stage
   - Role: Business Analyst / Product Owner
   - Goal: Business validation and sign-off
   - Mindset: Business language, user acceptance

7. **runtime-feedback-agent.md** - Runtime Feedback Stage
   - Role: DevOps / SRE / Production Support
   - Goal: Monitor production, close feedback loop
   - Mindset: Observability-focused, issue tracing

**Key Points:**
- Agents are **context/persona** Claude adopts
- Each agent has specific **responsibilities** and **ways of thinking**
- Agents are loaded for **specific stages** of the SDLC
- One agent active at a time (stage-specific)

---

## 🛠️ Skills = Capabilities/Tools (HOW)

**Definition:** Skills are **reusable capabilities** that perform specific tasks. They define HOW to accomplish something.

**Location:** `plugins/*/skills/` (41 skills across 7 plugins)

**Example Skills:**
- `requirement-extraction` - Extract REQ-* from raw intent
- `tdd-workflow` - Execute RED → GREEN → REFACTOR cycle
- `validate-test-coverage` - Check if coverage ≥80%
- `propagate-req-keys` - Tag code with REQ-* comments

**Key Points:**
- Skills are **actions/processes** to accomplish tasks
- Skills are **reusable** across different contexts
- Multiple skills can be used together
- Skills are available to **any agent** (or Claude directly)

---

## 🔗 The Relationship: Agents USE Skills

**Agents are personas that USE skills to accomplish their stage goals.**

```
Agent (WHO/WHAT) + Skills (HOW) = Stage Completion
```

### Example 1: Requirements Agent Uses Skills

**Scenario:** User says "I need a login feature"

**Requirements Agent** (persona/mindset):
- Thinks like a Business Analyst
- Focuses on extracting complete requirements
- Ensures testability and traceability

**Skills Used by Requirements Agent:**
1. `requirement-extraction` - Parse "login feature" → REQ-F-AUTH-001
2. `disambiguate-requirements` - Break into BR-*, C-*, F-*
3. `extract-business-rules` - Extract "password must be 8+ chars"
4. `validate-requirements` - Ensure unique keys, testable format
5. `create-traceability-matrix` - Map to upstream intent

**Output:**
```markdown
REQ-F-AUTH-001: User Login
  BR-AUTH-001: Password minimum 8 characters
  BR-AUTH-002: Email must be valid format
  C-AUTH-001: Max 5 login attempts per hour
  F-AUTH-001: session_timeout = max(user_idle, 30_minutes)
```

---

### Example 2: Code Agent Uses Skills

**Scenario:** Implement REQ-F-AUTH-001

**Code Agent** (persona/mindset):
- Thinks like a Developer
- TDD-first approach
- Quality-obsessed (7 Key Principles)

**Skills Used by Code Agent:**
1. `seven-questions-checklist` - Pre-coding quality gate
2. `tdd-workflow` - RED → GREEN → REFACTOR orchestrator
   - `red-phase` - Write failing test
   - `green-phase` - Minimal implementation
   - `refactor-phase` - Improve code
   - `commit-with-req-tag` - Commit with REQ-*
3. `propagate-req-keys` - Tag code: `# Implements: REQ-F-AUTH-001`
4. `apply-key-principles` - Validate against 7 principles
5. `autogenerate-from-business-rules` - Generate password validator from BR-AUTH-001

**Output:**
```python
# Implements: REQ-F-AUTH-001
# Validates: BR-AUTH-001, BR-AUTH-002
def login(email: str, password: str) -> LoginResult:
    # Auto-generated from BR-AUTH-001
    if len(password) < 8:
        raise ValueError("Password must be 8+ characters")

    # Auto-generated from BR-AUTH-002
    if not is_valid_email(email):
        raise ValueError("Invalid email format")

    # Implementation...
```

---

### Example 3: Runtime Feedback Agent Uses Skills

**Scenario:** Production alert "Auth timeout"

**Runtime Feedback Agent** (persona/mindset):
- Thinks like DevOps/SRE
- Traces issues back to requirements
- Creates feedback loop

**Skills Used by Runtime Feedback Agent:**
1. `trace-production-issue` - Alert → REQ-F-AUTH-001 → INT-001
2. `check-requirement-coverage` - Find all REQ-F-AUTH-001 artifacts
3. `refine-requirements` - Update requirements based on discovery
4. `requirement-extraction` - Create new intent: INT-042 "Fix auth timeout"

**Output:**
```
Production Alert: ERROR: req:REQ-F-AUTH-001 - Auth timeout after 30s
  ↓ [trace-production-issue]
Traced to: REQ-F-AUTH-001 "User login with email/password"
  ↓ [trace-production-issue]
Traced to: INT-001 "Customer self-service portal"
  ↓ [refine-requirements]
Updated: REQ-NFR-PERF-001 "Login must complete in <500ms"
  ↓ [requirement-extraction]
Created: INT-042 "Optimize auth performance"

→ [Cycle repeats with Requirements Agent...]
```

---

## 📊 Visual Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    7-STAGE AI SDLC                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
         ┌────────────────────────────────────────┐
         │         AGENTS (7 Personas)            │
         │  ┌──────────────────────────────────┐  │
         │  │ Requirements Agent               │  │
         │  │ Design Agent                     │  │
         │  │ Tasks Agent                      │  │
         │  │ Code Agent          ◄────────────┼──┼─── Active Persona
         │  │ System Test Agent                │  │
         │  │ UAT Agent                        │  │
         │  │ Runtime Feedback Agent           │  │
         │  └──────────────────────────────────┘  │
         └───────────────┬────────────────────────┘
                         │ USES
                         ▼
         ┌────────────────────────────────────────┐
         │         SKILLS (41 Capabilities)       │
         │  ┌──────────────────────────────────┐  │
         │  │ Foundation (3)                   │  │
         │  │ - requirement-traceability       │  │
         │  │ - check-requirement-coverage     │  │
         │  │ - propagate-req-keys             │  │
         │  ├──────────────────────────────────┤  │
         │  │ Quality Gate (2)                 │  │
         │  │ - seven-questions-checklist      │  │
         │  │ - apply-key-principles           │  │
         │  ├──────────────────────────────────┤  │
         │  │ Requirements (8)                 │  │
         │  │ - requirement-extraction         │  │
         │  │ - disambiguate-requirements      │  │
         │  │ - extract-business-rules         │  │
         │  │ - ...                            │  │
         │  ├──────────────────────────────────┤  │
         │  │ Design (3)                       │  │
         │  │ Code (21)                        │  │
         │  │ Testing (4)                      │  │
         │  │ Runtime (3)                      │  │
         │  └──────────────────────────────────┘  │
         └────────────────────────────────────────┘
```

---

## 🎯 Key Differences

| Aspect | Agents | Skills |
|--------|--------|--------|
| **What** | Persona/Role | Capability/Tool |
| **Purpose** | Define WHO and WHAT | Define HOW |
| **Scope** | Stage-specific | Cross-cutting, reusable |
| **Count** | 7 (one per stage) | 41 (many capabilities) |
| **Activation** | One at a time (stage) | Many at once (as needed) |
| **Loading** | Via agent files or stage switch | Via plugins |
| **Example** | "Code Agent" persona | "tdd-workflow" skill |
| **Mindset** | Developer thinking | Process execution |
| **Lifespan** | Active for entire stage | Used momentarily when needed |

---

## 🔄 How They Work Together

### Pattern 1: Agent Orchestrates Skills

**Requirements Agent** needs to create requirements:
```
Requirements Agent (persona) says:
"I need to extract requirements from this user story"

→ Loads skill: requirement-extraction
→ Executes: Parse story, create REQ-* keys
→ Loads skill: validate-requirements
→ Executes: Check uniqueness, testability
→ Loads skill: create-traceability-matrix
→ Executes: Map to upstream intent

Requirements Agent returns:
"Created REQ-F-AUTH-001 with full traceability"
```

### Pattern 2: Skills Used Independently

You can use skills **without** loading an agent:

```
You: "Check requirement coverage for REQ-F-AUTH-001"

Claude directly:
→ Loads skill: check-requirement-coverage
→ Executes: Scan codebase for REQ-F-AUTH-001
→ Returns: "Coverage: 85% (design ✅, code ✅, tests ✅)"

(No agent persona required)
```

### Pattern 3: Agent Switching Uses Different Skills

As you move through stages, agents switch and use different skill sets:

```
Stage 1: Requirements Agent
  Skills: requirement-extraction, validate-requirements

Stage 2: Design Agent
  Skills: design-with-traceability, create-adrs

Stage 4: Code Agent
  Skills: tdd-workflow, apply-key-principles, autogenerate-*

Stage 5: System Test Agent
  Skills: bdd-workflow, validate-test-coverage, run-integration-tests

Stage 7: Runtime Feedback Agent
  Skills: telemetry-tagging, trace-production-issue
```

---

## 🎓 Simple Analogy

**Think of building a house:**

**Agents = Construction Crew Roles**
- Architect (Design Agent)
- Carpenter (Code Agent)
- Electrician (System Test Agent)
- Inspector (UAT Agent)

**Skills = Tools/Techniques**
- Hammer, Saw, Drill (tools)
- Framing technique, Wiring technique (processes)
- Quality checks, Safety inspections (validations)

**How they work together:**
- The **Carpenter** (Code Agent) uses the **Hammer** (tdd-workflow skill) to build the frame
- The **Electrician** (System Test Agent) uses **Wire Strippers** (bdd-workflow skill) to install wiring
- The **Inspector** (UAT Agent) uses **Checklist** (validate-requirements skill) to verify compliance

**Key insight:**
- Different roles (agents) can use the **same tools** (skills)
- One role (agent) uses **multiple tools** (skills) to complete their work
- Tools (skills) are reusable across roles (agents)

---

## 📋 Practical Usage

### When to Use Agents

Load an agent when you want Claude to **think like a specific role** for a stage:

```bash
# Enter Design Stage
/agent load design-agent

# Claude now thinks like an architect
# Focuses on: components, APIs, data models, ADRs
# Uses design-skills naturally
```

### When to Use Skills Directly

Invoke a skill when you want a **specific capability** without stage context:

```bash
# Just check coverage, no role needed
/skill invoke check-requirement-coverage

# Or ask naturally
You: "Check coverage for REQ-F-AUTH-001"
```

### When to Use Both

Move through stages with agents, each using appropriate skills:

```
Stage 1: /agent load requirements-agent
  → Uses requirement-extraction, validate-requirements

Stage 2: /agent load design-agent
  → Uses design-with-traceability, create-adrs

Stage 4: /agent load code-agent
  → Uses tdd-workflow, apply-key-principles

Stage 7: /agent load runtime-feedback-agent
  → Uses trace-production-issue
  → Creates new intent → back to Stage 1
```

---

## ✅ Summary

| Concept | Explanation |
|---------|-------------|
| **Agents** | 7 role-based personas for SDLC stages (WHO/WHAT) |
| **Skills** | 41 reusable capabilities (HOW) |
| **Relationship** | Agents USE skills to accomplish stage goals |
| **Agents are** | Context/mindset/focus for Claude |
| **Skills are** | Actions/processes Claude executes |
| **Agent loading** | `/agent load NAME` or stage transition |
| **Skill loading** | Automatic via plugins (always available) |
| **Agent switching** | One at a time (stage-based) |
| **Skill usage** | Many at once (as needed) |
| **Independent use** | Skills YES, Agents optional |

**Key Takeaway:**
- **Agents** = The role Claude plays (persona)
- **Skills** = The capabilities Claude has (toolbox)
- **Together** = Role-appropriate use of capabilities to complete SDLC stages

---

**Version:** 1.0.0
**Last Updated:** 2025-11-23
