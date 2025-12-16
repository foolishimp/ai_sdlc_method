# TCS-012: Context Snapshot and Recovery

**Test Case Specification**
**Component**: Context Snapshot Command (`/aisdlc-snapshot-context`)
**Requirement**: REQ-TOOL-012.0.1.0 - Context Snapshot and Recovery
**Status**: 📋 Specified
**Created**: 2025-12-16
**Author**: System Test Agent

---

## Purpose

Validate the `/aisdlc-snapshot-context` command implementation, which captures immutable snapshots of the current session context including tasks, work state, decisions, and git status.

---

## Scope

### In Scope
- Command availability and execution
- Snapshot file creation and naming
- Template variable substitution
- Directory structure creation
- Task context gathering
- Conversation context analysis
- Git context integration
- Error handling
- Recovery guidance generation
- Integration with `/aisdlc-checkpoint-tasks`
- Archival and retention policy

### Out of Scope
- Actual conversation history API (simulated in tests)
- Production archival automation (future enhancement)
- Snapshot index file (future enhancement)
- File permissions on non-Unix systems

---

## Test Scenarios

| ID | Scenario | Input State | Expected Output | Priority |
|----|----------|-------------|-----------------|----------|
| SS-001 | Basic snapshot creation | Valid workspace with tasks | Snapshot created successfully | High |
| SS-002 | Snapshot with empty workspace | Workspace with no tasks | Snapshot with default values | High |
| SS-003 | Snapshot filename format | Command execution | `{YYYYMMDD}_{HHMM}_{label}.md` | High |
| SS-004 | Snapshot directory creation | No context_history directory | Directory auto-created | High |
| SS-005 | Task context gathering | 5 tasks (2 in-progress, 2 pending, 1 blocked) | All tasks captured with status | High |
| SS-006 | Git context integration | Modified, staged, untracked files | All file states captured | Medium |
| SS-007 | Template variable substitution | All template variables | All placeholders replaced | High |
| SS-008 | Error: workspace not initialized | No .ai-workspace directory | Error message displayed | High |
| SS-009 | Error: cannot write snapshot | Read-only directory | Error message with troubleshooting | Medium |
| SS-010 | Warning: template not found | Missing template file | Built-in template used | Medium |
| SS-011 | Warning: git not available | Non-git directory | Git section shows fallback | Low |
| SS-012 | Warning: ACTIVE_TASKS missing | Missing tasks file | Snapshot with empty task data | Medium |
| SS-013 | Snapshot includes recovery guidance | Valid snapshot | Recovery commands included | High |
| SS-014 | Multiple snapshots tracking | Create 3 snapshots | Snapshots linked via metadata | Medium |
| SS-015 | Immutability verification | Attempt to modify snapshot | File read-only (if supported) | Low |
| SS-016 | Integration with checkpoint | Run checkpoint then snapshot | Snapshot reflects checkpoint | High |
| SS-017 | Conversation markers extraction | Work session with decisions | Decisions captured in snapshot | Medium |
| SS-018 | Open questions tracking | Session with unresolved questions | Questions listed in snapshot | Medium |
| SS-019 | Blockers identification | Tasks with blockers | Blockers documented in snapshot | Medium |
| SS-020 | Recent finished tasks | 3 finished tasks exist | Tasks listed in snapshot | Low |
| SS-021 | Snapshot metadata accuracy | Valid session | Message count, duration tracked | Low |
| SS-022 | Archival check suggestion | >50 snapshots exist | Archival suggestion shown | Low |
| SS-023 | Old snapshot detection | Snapshots >30 days old | Archival candidates identified | Low |
| SS-024 | Success message display | Snapshot created | Formatted success message | Medium |
| SS-025 | Empty git status | No file changes | Empty git sections with "(None)" | Low |

---

## Test Data

### Sample ACTIVE_TASKS.md
```markdown
# Active Tasks

*Last Updated: 2025-12-16 10:30*

---

## Task #1: Implement User Authentication

**Priority**: High
**Status**: In Progress
**Requirements**: REQ-F-AUTH-001, REQ-NFR-SEC-001

**Description**:
Implement JWT-based user authentication.

---

## Task #2: Add Database Schema

**Priority**: Medium
**Status**: Pending
**Requirements**: REQ-F-DATA-001

**Description**:
Create user and session tables.

---

## Task #3: Fix Login Bug

**Priority**: High
**Status**: Blocked
**Blocker**: Waiting for security review
**Requirements**: REQ-F-AUTH-002

**Description**:
Fix timeout issue in login flow.

---

## Summary

**Total Active Tasks**: 3
- In Progress: 1
- Pending: 1
- Blocked: 1
```

### Sample Git Status
```
On branch feature/auth-service
Your branch is up to date with 'origin/feature/auth-service'.

Changes not staged for commit:
  modified:   src/auth/auth_service.py
  modified:   tests/auth/test_auth_service.py

Untracked files:
  src/auth/jwt_utils.py
```

### Sample Finished Tasks
```
.ai-workspace/tasks/finished/
├── 20251215_1400_setup_project.md
├── 20251215_1530_add_dependencies.md
└── 20251216_0900_initial_tests.md
```

### Sample Snapshot Filenames
```
.ai-workspace/context_history/
├── 20251216_1430_implementing_auth_service.md
├── 20251216_1000_fixing_payment_tests.md
├── 20251215_1700_context_snapshot.md  # Default label when no focus
└── README.md
```

---

## Acceptance Criteria

### AC-001: Command Availability
- **Given** AISDLC methodology plugin is installed
- **When** user types `/aisdlc-snapshot-context`
- **Then** command is recognized and executed

### AC-002: Snapshot File Creation
- **Given** valid workspace exists
- **When** command is executed
- **Then** snapshot file created at `.ai-workspace/context_history/{YYYYMMDD}_{HHMM}_{label}.md`

### AC-003: Filename Format
- **Given** snapshot is created
- **When** examining filename
- **Then** format matches `{YYYYMMDD}_{HHMM}_{label}.md` exactly (follows finished task convention)

### AC-004: Directory Auto-Creation
- **Given** no `context_history/` directory exists
- **When** command is executed
- **Then** directory structure is created automatically

### AC-005: Task Context Accuracy
- **Given** ACTIVE_TASKS.md with 5 tasks (2 in-progress, 2 pending, 1 blocked)
- **When** snapshot is created
- **Then** all tasks appear in snapshot grouped by status
- **And** task counts are accurate

### AC-006: Template Variable Substitution
- **Given** template contains `{PROJECT_NAME}`, `{TIMESTAMP}`, etc.
- **When** snapshot is generated
- **Then** all variables replaced with actual values
- **And** no placeholder text like "{...}" remains

### AC-007: Error Handling - No Workspace
- **Given** no `.ai-workspace` directory exists
- **When** command is executed
- **Then** error message "❌ Workspace not initialized. Run /aisdlc-init first." is shown
- **And** no snapshot file is created

### AC-008: Warning Handling - Missing Template
- **Given** template file does not exist
- **When** command is executed
- **Then** warning "⚠️ Template not found, using built-in template" is shown
- **And** snapshot created using built-in template

### AC-009: Git Integration
- **Given** git repository with modified, staged, and untracked files
- **When** snapshot is created
- **Then** all three file states are captured correctly
- **And** current branch is identified

### AC-010: Recovery Guidance
- **Given** any snapshot is created
- **When** examining snapshot contents
- **Then** "Recovery Guidance" section exists
- **And** includes commands to restore context
- **And** includes suggested message for Claude

### AC-011: Immutability
- **Given** snapshot file is created
- **When** snapshot is written
- **Then** file permissions set to read-only (on supported platforms)
- **Or** warning logged if not supported

### AC-012: Success Message
- **Given** snapshot created successfully
- **When** command completes
- **Then** formatted success message displayed
- **And** message includes snapshot ID, location, and contents summary

### AC-013: Integration with Checkpoint
- **Given** tasks have been checkpointed
- **When** snapshot command is run
- **Then** snapshot reflects checkpointed task status
- **And** recently finished tasks are listed

### AC-014: Conversation Markers
- **Given** work session with decisions and questions
- **When** snapshot is created
- **Then** decisions are listed in "Key Decisions Made"
- **And** questions are listed in "Open Questions"

### AC-015: Default Values
- **Given** no git available
- **When** snapshot is created
- **Then** git fields show "(Git not available)"
- **And** snapshot creation continues without error

---

## Test Environment

### Prerequisites
- Python 3.9+
- pytest-bdd
- Git installed
- AISDLC methodology plugin installed

### Setup
```bash
# Create test workspace
mkdir -p /tmp/test_workspace/.ai-workspace/tasks/{active,finished}
mkdir -p /tmp/test_workspace/.ai-workspace/templates
mkdir -p /tmp/test_workspace/.ai-workspace/context_history

# Initialize git
cd /tmp/test_workspace
git init
git config user.email "test@test.com"
git config user.name "Test User"

# Create initial files
touch .ai-workspace/tasks/active/ACTIVE_TASKS.md
touch .ai-workspace/templates/CONTEXT_SNAPSHOT_TEMPLATE.md
```

### Teardown
```bash
# Clean up test workspace
rm -rf /tmp/test_workspace
```

---

## Validation Approach

### Manual Testing
1. Execute `/aisdlc-snapshot-context` in test environment
2. Verify snapshot file created with correct filename format: `{YYYYMMDD}_{HHMM}_{label}.md`
3. Verify snapshot stored in flat `.ai-workspace/context_history/` directory (not subdirectory)
4. Inspect snapshot contents for completeness
5. Verify all template variables substituted
6. Test error conditions manually

### Automated Testing
1. **BDD Scenarios** (Gherkin)
   - Located: `claude-code/tests/features/system-test/context_snapshot.feature`
   - Uses pytest-bdd framework
   - Follows Given/When/Then pattern

2. **Step Definitions** (Python)
   - Located: `claude-code/tests/features/steps/context_snapshot_steps.py`
   - Implements scenario steps
   - Uses pytest fixtures for setup/teardown

3. **Test Execution**
   ```bash
   # Run all context snapshot tests
   pytest claude-code/tests/features/system-test/context_snapshot.feature -v

   # Run specific scenario by tag
   pytest -m snapshot_creation

   # Run with coverage
   pytest --cov=.ai-workspace claude-code/tests/features/
   ```

### Key Test Validations
1. **Filename Format**: Must match `{YYYYMMDD}_{HHMM}_{label}.md` (e.g., `20251216_1430_context_snapshot.md`)
2. **Storage Location**: Flat directory `.ai-workspace/context_history/` (not `snapshots/` subdirectory)
3. **Label Derivation**: Default to `context_snapshot` when no work focus is clear
4. **Template Variables**: All `{VARIABLE}` placeholders must be replaced

---

## Coverage Requirements

### Functional Coverage
- ✅ Command execution: 100%
- ✅ File creation: 100%
- ✅ Template substitution: 100%
- ✅ Error handling: 100%
- ✅ Git integration: 90% (platform-specific variations)
- ✅ Recovery guidance: 100%

### Edge Cases
- Empty workspace (no tasks)
- Missing template file
- Git not available
- Read-only filesystem
- Very long task titles (>200 chars)
- Special characters in task titles
- Concurrent snapshot creation attempts
- Filesystem full condition

---

## Traceability

### Requirements
- REQ-TOOL-012.0.1.0: Context Snapshot and Recovery
- REQ-TOOL-002: Developer Workspace
- REQ-TOOL-003: Workflow Commands

### Design Documents
- Command Specification: `claude-code/.claude-plugin/plugins/aisdlc-methodology/commands/aisdlc-snapshot-context.md`
- Template: `.ai-workspace/templates/CONTEXT_SNAPSHOT_TEMPLATE.md`

### Related Tests
- TCS-001: Status Command (uses similar task parsing)
- TCS-002: Checkpoint Command (integration point)
- TCS-007: Update Command (snapshot preservation)

---

## Notes

### Implementation Considerations
1. **Conversation Analysis**: Limited to pattern matching in tests (no LLM API)
2. **Timestamp Accuracy**: Use fixed timestamps in tests for reproducibility
3. **File Permissions**: Platform-dependent; mock on Windows
4. **Filename Convention**: Follows finished task convention for consistency
5. **Label Derivation**: Extract from work context or use default `context_snapshot`

### Known Limitations
1. Cannot fully test conversation history API integration (not available in test environment)
2. Session duration estimation is approximate
3. Message count requires conversation API access
4. Label derivation requires conversation context analysis

### Future Enhancements
1. Snapshot index file (`.snapshot_index.yml`)
2. Automated archival (manual for now)
3. Snapshot comparison tool
4. Snapshot restoration command
5. Snapshot search functionality
6. Intelligent label derivation from conversation context

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-16 | Initial specification |

---

**End of TCS-012**
