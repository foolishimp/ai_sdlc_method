# ADR-005: Iterative Refinement via Stage Feedback Loops

**Status**: Accepted
**Date**: 2025-11-25
**Deciders**: Development Tools Team
**Requirements**: **MISSING** - REQ-NFR-REFINE-001 (needs to be created)
**Depends On**: ADR-003 (Agents for Stage Personas)

---

## Context

The AISDLC methodology has 7 sequential stages. Traditional waterfall approach assumes each stage is complete before proceeding to next. However, reality shows:

1. **Requirements are discovered during design** - "How will users reset passwords?" reveals missing REQ-F-AUTH-003
2. **Design gaps found during coding** - "Need error handling component" reveals missing design
3. **Requirements ambiguity found during testing** - "What exactly is 'fast login'?" needs refinement to "< 500ms"
4. **Production issues reveal requirement gaps** - "Auth timeout" creates new intent

**Problem**: How do we achieve completeness if we only go forward through stages?

---

## Decision

**We will implement bidirectional feedback loops where each agent has the DEFAULT BEHAVIOR to feedback to prior stages when gaps/ambiguities are discovered.**

This is not optional - it's **core agent behavior** for achieving completeness.

---

## The Feedback Architecture

### Pattern: Continuous Refinement

```
Stage 1: Requirements
    ↓ (requirements)
Stage 2: Design ─────────────┐
    ↓ (design)               │ Discovers:
Stage 3: Tasks ──────────────┤ "Missing requirement!"
    ↓ (work units)           │
Stage 4: Code ───────────────┤ Feedback
    ↓ (implementation)       │
Stage 5: System Test ────────┤ →→→ Back to Stage 1
    ↓ (BDD scenarios)        │     (Requirements Agent)
Stage 6: UAT ────────────────┤
    ↓ (sign-off)             │     Creates/Refines
Stage 7: Runtime ────────────┘     REQ-*
    ↓                              ↓
New Intent                     Continue forward
```

**Key Principle**: **Discovery is inevitable. Feedback enables completeness.**

---

## Rationale

### Why Bidirectional (vs Waterfall)

**Waterfall Assumption**:
"Get requirements 100% right upfront, then never change them"

**Reality**:
- Requirements ambiguity discovered during design
- Edge cases discovered during coding
- Test scenarios reveal missing acceptance criteria
- Production reveals performance requirements not captured

**AISDLC Approach**:
"Start with best understanding, refine continuously through feedback"

### How This Achieves Completeness

**Scenario 1: Design → Requirements Feedback**

```
Design Agent (Stage 2):
"I'm designing AuthenticationService for REQ-F-AUTH-001...

Wait - the requirement says 'user can log in' but doesn't specify:
- What if login fails? (error handling requirement missing)
- What if password forgotten? (password reset requirement missing)
- What if account locked? (account management requirement missing)

FEEDBACK TO REQUIREMENTS AGENT:
'REQ-F-AUTH-001 is ambiguous. Need requirements for:
 - Error handling
 - Password reset
 - Account lockout'
```

**Requirements Agent Response**:
```
Creates new requirements:
- REQ-F-AUTH-002: Login error handling
- REQ-F-AUTH-003: Password reset flow
- REQ-NFR-SEC-002: Account lockout after 5 failures

Updates traceability matrix
Returns to Design Agent: "Requirements refined, continue design"
```

**Scenario 2: Code → Design Feedback**

```
Code Agent (Stage 4):
"Implementing LoginService per design...

Wait - the design specifies JWT tokens but doesn't specify:
- Token expiration strategy
- Refresh token mechanism
- Token storage location

FEEDBACK TO DESIGN AGENT:
'Authentication design incomplete. Need specifications for token lifecycle'
```

**Design Agent Response**:
```
Updates design:
- Component: TokenManager
- API: POST /auth/refresh
- Data: refresh_tokens table

Updates traceability, returns to Code Agent
```

**Scenario 3: Test → Requirements Feedback**

```
System Test Agent (Stage 5):
"Creating BDD scenarios for REQ-NFR-PERF-001: 'Login must be fast'

Wait - 'fast' is ambiguous. Cannot write testable scenario.

FEEDBACK TO REQUIREMENTS AGENT:
'REQ-NFR-PERF-001 not testable. Define 'fast' with measurable criteria'
```

**Requirements Agent Response**:
```
Refines requirement:
REQ-NFR-PERF-001 v2: "Login response time < 500ms (p95) under normal load"

Acceptance Criteria:
- p95 latency < 500ms
- Measured with 1000 concurrent users
- Load test passes before deployment

Returns to System Test Agent: "Requirement refined, now testable"
```

---

## Design Decision: Universal Default Behavior

**Every agent has this in their core responsibilities:**

```markdown
## Core Responsibilities

1. [Stage-specific primary work]
2. [Stage-specific outputs]
3. [Stage-specific quality gates]
4. **Process Feedback from Downstream Stages** ← UNIVERSAL
5. **Provide Feedback to Upstream Stages** ← UNIVERSAL
```

**This is NOT optional. This is HOW we achieve completeness.**

---

## Rejected Alternatives

### Alternative 1: Waterfall (No Feedback)
**Approach**: Each stage completes fully before next stage begins. No going back.

**Why Rejected**:
- ❌ Impossible to get requirements 100% right upfront
- ❌ Design discovers requirement gaps
- ❌ Code discovers design gaps
- ❌ Tests discover ambiguities
- ❌ Production reveals missing requirements
- ❌ Results in incomplete/ambiguous specs

**Lesson**: Feedback loops are essential for quality

### Alternative 2: Feedback Only at Stage End
**Approach**: Collect all feedback, batch update previous stage at end

**Why Rejected**:
- ❌ Delays discovery (waste time on flawed design)
- ❌ Harder to context-switch back
- ❌ Batching loses immediacy

**Better**: Feedback immediately when discovered

### Alternative 3: Separate "Refinement Stage"
**Approach**: Add Stage 8: Refinement where all feedback is processed

**Why Rejected**:
- ❌ Adds unnecessary stage
- ❌ Delays refinement
- ❌ Confuses flow (which stage am I in?)

**Better**: Refinement happens inline, immediately

### Alternative 4: External Change Request Process
**Approach**: Formal CR process (like traditional SDLC) for requirement changes

**Why Rejected**:
- ❌ Too heavyweight for iterative discovery
- ❌ Bureaucratic overhead
- ❌ Slows down development
- ❌ Not agile

**Better**: Lightweight, immediate feedback

---

## Implementation in Agent Files

**Every agent file has:**

```markdown
## Inputs You Receive

1. [Primary inputs from previous stage]
2. [Context from configuration]
3. [Standards/templates]
4. **Feedback from Downstream Stages**: ← UNIVERSAL
   - Design: "Missing requirements for error handling"
   - Code: "Requirement ambiguous, needs clarification"
   - Test: "Acceptance criteria not testable"
   - Runtime: "Performance requirement not met in production"
```

**Feedback handling:**

```markdown
### Step 6: Process Feedback ← UNIVERSAL STEP

When feedback arrives from downstream stages:
- Update requirement if clarification needed
- Create new requirement if gap discovered
- Version requirement if changed (REQ-F-AUTH-001 v2)
- Update traceability matrix
- Notify affected downstream stages
```

---

## Design Pattern: Feedback Message Format

**Standardized feedback structure:**

```yaml
feedback:
  from_stage: "code"  # Which stage is providing feedback
  from_agent: "Code Agent"
  to_stage: "requirements"
  to_agent: "Requirements Agent"

  type: "gap"  # gap | ambiguity | clarification | error

  requirement_id: "REQ-F-AUTH-001"

  issue: "Requirement doesn't specify error handling for login failures"

  context:
    - "Implementing login() function"
    - "Need to handle: wrong password, account locked, network timeout"

  request:
    - "Create REQ-F-AUTH-002 for error handling"
    - "Or add acceptance criteria to REQ-F-AUTH-001"

  blocking: false  # Can I continue or must wait?
```

---

## Consequences

### Positive

✅ **Achieves True Completeness**
- Requirements evolve based on real discovery
- Design refines based on implementation reality
- System reaches completeness iteratively

✅ **Reduces Waste**
- Don't design what isn't needed
- Don't implement incomplete designs
- Don't test ambiguous requirements

✅ **Continuous Improvement**
- Each stage improves previous stages
- Knowledge accumulates
- Quality increases over time

✅ **Reality-Based**
- Acknowledges we can't know everything upfront
- Embraces discovery
- Adapts to learning

✅ **Traceability Maintained**
- Feedback is documented
- Requirement versions tracked
- Change history preserved

### Negative

⚠️ **Potential Infinite Loops**
- Design → Requirements → Design → Requirements → ...
- Need termination conditions

**Mitigation**:
- Quality gates prevent infinite loops
- Each iteration should reduce ambiguity
- Maximum 3 iterations suggested

⚠️ **Context Switching**
- Designer must switch to Requirements Agent
- Breaks flow momentarily

**Mitigation**:
- Lightweight feedback (just create requirement)
- Can continue design in parallel
- Feedback is asynchronous

⚠️ **Version Proliferation**
- Requirements could have many versions
- REQ-F-AUTH-001 v1, v2, v3, v4...

**Mitigation**:
- Version only when substantive change
- Clarifications update existing (not version)
- Document version history

---

## Examples of Feedback in Practice

### Example 1: Code Agent → Requirements Agent

```
Code Agent discovers during TDD:
"REQ-F-AUTH-001 acceptance criteria says 'valid credentials'
 but doesn't define what makes credentials valid.

 Feedback to Requirements Agent:
 - Add acceptance criteria: Email format validation
 - Add acceptance criteria: Password minimum 8 characters
 - Or create REQ-DATA-AUTH-001 for data validation rules"

Requirements Agent refines:
REQ-F-AUTH-001 v1 → v2 (added specific validation criteria)
Created: REQ-DATA-AUTH-001 (email validation)
```

### Example 2: Design Agent → Requirements Agent (This Session!)

```
Design Agent (me, just now):
"Reviewing 16 requirements for design...

Discovered gaps:
- Command system design exists but REQ-F-CMD-001 underspecified
- Testing requirements exist but no architecture details
- Traceability requirements exist but mechanism not specified

Wait - these aren't requirement gaps. These are design details.
The REQUIREMENTS are correct. I need to DESIGN the solution.

No feedback needed to Requirements Agent.
Continue with design."
```

**Lesson**: Not every design question is a requirement gap!

### Example 3: UAT Agent → Requirements Agent

```
UAT Agent during business validation:
"Testing REQ-F-AUTH-001 with business stakeholders...

Business says: 'We also need social login (Google, Facebook)'

This is NEW functionality not in original intent.

FEEDBACK TO REQUIREMENTS AGENT:
'Business requested social login during UAT.
 Should we:
 1. Create REQ-F-AUTH-004: Social login
 2. Defer to next iteration (new intent)
 3. Mark as out of scope for this intent'
```

Requirements Agent decides (with Product Owner input).

---

## Quality Gates for Feedback

**When to provide feedback upstream:**
- ✅ Missing requirement (gap)
- ✅ Ambiguous requirement (needs clarification)
- ✅ Untestable requirement (needs measurable criteria)
- ✅ Conflicting requirements (needs resolution)

**When NOT to provide feedback:**
- ❌ Design implementation details (just design it)
- ❌ Code structure choices (designer's decision)
- ❌ Testing framework choice (tester's decision)

**Guideline**: Feedback for WHAT (requirements), not HOW (implementation)

---

## Missing Requirement Detected!

**🚨 Design Agent Feedback to Requirements Agent:**

We need a requirement that specifies this feedback loop behavior:

```markdown
### REQ-NFR-REFINE-001: Iterative Refinement via Stage Feedback

**Priority**: Critical
**Type**: Non-Functional (Process)

**Description**: The system shall support bidirectional feedback where downstream stages can provide feedback to upstream stages for iterative refinement.

**Acceptance Criteria**:
- [ ] Every agent specifies "Process Feedback" in core responsibilities
- [ ] Feedback format standardized (gap, ambiguity, clarification, error)
- [ ] Requirements Agent accepts feedback from all 6 downstream stages
- [ ] Design Agent accepts feedback from 5 downstream stages
- [ ] Feedback results in requirement/design updates (versioned)
- [ ] Traceability maintained through feedback cycles

**Rationale**: Feedback loops enable discovery-driven completeness. Cannot achieve complete requirements upfront - must refine based on downstream learning.

**Examples**:
- Code Agent discovers requirement ambiguity → Requirements Agent clarifies
- Test Agent finds untestable criteria → Requirements Agent refines
- Design Agent finds requirement gap → Requirements Agent creates new REQ-*
```

**Should this requirement be added to AISDLC_IMPLEMENTATION_REQUIREMENTS.md?**

---

**Status**: ✅ Accepted as design pattern
**Next**: Formalize as requirement (Requirements Agent work)
