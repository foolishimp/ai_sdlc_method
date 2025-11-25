# Feedback Protocol

Bidirectional feedback rules for iterative refinement (REQ-NFR-REFINE-001).

## Purpose

Close feedback loops between SDLC stages to:
- Identify gaps before they become bugs
- Clarify ambiguities before implementation
- Propagate learning across stages
- Maintain requirement quality

## Feedback Types

| Type | Description | Example |
|------|-------------|---------|
| `gap` | Something missing entirely | "No REQ for error handling" |
| `ambiguity` | Something unclear/vague | "What does 'fast' mean?" |
| `clarification` | Need more detail | "Which auth methods supported?" |
| `error` | Something incorrect | "API spec doesn't match design" |
| `conflict` | Contradictory specs | "REQ-001 conflicts with REQ-002" |

## Feedback Format

```
FEEDBACK to <Stage Agent>:
Type: <gap|ambiguity|clarification|error|conflict>
REQ: <REQ-* key if applicable>
Issue: <Clear description>
Suggestion: <Proposed resolution>
```

## Stage-Specific Feedback

### Requirements Agent (Stage 1)

**Receives feedback from**:
- Design: "Requirement unclear, need measurable criteria"
- Code: "Missing requirement for feature X"
- Test: "Acceptance criteria not testable"
- UAT: "Business process not covered"
- Runtime: "Production issue needs new requirement"

**Sends feedback to**:
- Intent Manager: "Intent ambiguous, need clarification"

### Design Agent (Stage 2)

**Receives feedback from**:
- Tasks: "Design incomplete for implementation"
- Code: "API spec missing error responses"
- Test: "Integration points not specified"
- Runtime: "Scalability design insufficient"

**Sends feedback to**:
- Requirements: "REQ-* needs clarification"
- Requirements: "Missing requirement discovered"

### Tasks Agent (Stage 3)

**Receives feedback from**:
- Code: "Task blocked by dependency"
- Code: "Task scope too large"

**Sends feedback to**:
- Design: "Design detail missing for task"
- Requirements: "Task reveals missing REQ"

### Code Agent (Stage 4)

**Receives feedback from**:
- Test: "Test failing, implementation bug"
- Test: "Edge case not handled"
- Runtime: "Performance issue in production"

**Sends feedback to**:
- Design: "Design gap discovered"
- Tasks: "Task blocked"
- Requirements: "REQ ambiguous"

### System Test Agent (Stage 5)

**Receives feedback from**:
- UAT: "Integration doesn't match business flow"
- Runtime: "Test environment differs from prod"

**Sends feedback to**:
- Code: "Bug found in implementation"
- Design: "Integration spec missing"

### UAT Agent (Stage 6)

**Receives feedback from**:
- Runtime: "User behavior differs from UAT assumptions"

**Sends feedback to**:
- Requirements: "Business process gap"
- Design: "UX doesn't match expectations"

### Runtime Agent (Stage 7)

**Sends feedback to**:
- All stages: Production issues with REQ-* traceability
- Requirements: New intent from production findings

## When Feedback Arrives

1. **Pause** current work
2. **Analyze** - Is this my responsibility or upstream?
3. **Decide**:
   - My gap → Fix and document
   - Upstream gap → Forward feedback
4. **Update** affected artifacts
5. **Notify** related stages
6. **Resume** current work

## Feedback Examples

### Code → Requirements
```
FEEDBACK to Requirements Agent:
Type: gap
REQ: (none - missing)
Issue: Implementing login but no REQ for account lockout after failed attempts
Suggestion: Create REQ-F-AUTH-002 for account lockout policy
```

### Test → Code
```
FEEDBACK to Code Agent:
Type: error
REQ: REQ-F-AUTH-001
Issue: test_login_timeout fails - login() doesn't handle network timeout
Suggestion: Add timeout handling to login() function
```

### Runtime → Design
```
FEEDBACK to Design Agent:
Type: gap
REQ: REQ-NFR-PERF-001
Issue: Production shows 2s latency under load, design assumed 100 concurrent users but we have 10,000
Suggestion: Review caching and connection pooling design
```

## Quality Gates

Every stage includes:
- [ ] All feedback processed (upstream and downstream)
- [ ] No unresolved gaps
- [ ] No unresolved ambiguities
- [ ] Traceability updated

## Remember

- Feedback is healthy, not criticism
- Early feedback prevents late bugs
- Every gap found is a bug prevented
- Traceability enables feedback routing
