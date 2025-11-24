# Task: Rename Persona Commands with aisdlc- Prefix

**Status**: Completed
**Date**: 2025-11-25
**Time**: 03:05
**Actual Time**: 0.5 hours (Estimated: 0.5 hours)

**Task ID**: #6
**Requirements**: REQ-F-CMD-002

---

## Problem

Persona commands had inconsistent naming - they lacked the `aisdlc-` prefix used by all other framework commands:
- `apply-persona.md` (should be `aisdlc-apply-persona.md`)
- `list-personas.md` (should be `aisdlc-list-personas.md`)
- `persona-checklist.md` (should be `aisdlc-persona-checklist.md`)
- `switch-persona.md` (should be `aisdlc-switch-persona.md`)

This inconsistency made it unclear which commands were part of the ai_sdlc_method framework vs. potentially from other sources.

---

## Investigation

1. **Analyzed** command inventory - found 10 commands total
   - 6 with `aisdlc-` prefix (consistent)
   - 4 without prefix (persona commands - inconsistent)
2. **Reviewed** origin - these commands were created before `aisdlc-` prefix convention was established
3. **Checked** REQ-F-CMD-002 - Persona Management is part of MVP (formerly CMD-003)
4. **Validated** setup_commands.py doesn't hardcode names - dynamically lists from directory

---

## Solution

**Refactoring Changes**:
- Renamed 4 persona command files with `aisdlc-` prefix
- Updated templates/claude/.claude/commands/ (dogfooding)
- Updated setup_commands.py docstring and examples
- Updated cross-references within persona command files

**TDD Process**:
N/A - Refactoring task, no code changes

---

## Files Modified

**Main commands:**
- `.claude/commands/apply-persona.md` → `aisdlc-apply-persona.md` (RENAMED)
- `.claude/commands/list-personas.md` → `aisdlc-list-personas.md` (RENAMED)
- `.claude/commands/persona-checklist.md` → `aisdlc-persona-checklist.md` (RENAMED)
- `.claude/commands/switch-persona.md` → `aisdlc-switch-persona.md` (RENAMED)

**Template commands:**
- `templates/claude/.claude/commands/apply-persona.md` → `aisdlc-apply-persona.md` (RENAMED)
- `templates/claude/.claude/commands/list-personas.md` → `aisdlc-list-personas.md` (RENAMED)
- `templates/claude/.claude/commands/persona-checklist.md` → `aisdlc-persona-checklist.md` (RENAMED)
- `templates/claude/.claude/commands/switch-persona.md` → `aisdlc-switch-persona.md` (RENAMED)

**Installer:**
- `installers/setup_commands.py` - Updated docstring and next steps (MODIFIED)

**Command cross-references:**
- Updated all 4 persona commands to reference new names
- Used sed to update all occurrences: `/apply-persona` → `/aisdlc-apply-persona`, etc.

---

## Test Coverage

N/A - Refactoring task

**Validation**:
- ✅ Verified all 4 commands renamed in both locations
- ✅ Confirmed cross-references updated
- ✅ Checked installer no longer references old command names

---

## Feature Flag

N/A - Refactoring task

---

## Testing

**Manual Testing**:
```bash
# Verify renamed files exist
ls -1 .claude/commands/ | grep persona

# Result:
# aisdlc-apply-persona.md
# aisdlc-list-personas.md
# aisdlc-persona-checklist.md
# aisdlc-switch-persona.md
```

**Results**:
- All 4 commands renamed ✅
- Templates synced ✅
- Installer updated ✅
- Cross-references updated ✅

---

## Result

✅ **Task completed successfully**
- All persona commands now have consistent `aisdlc-` prefix
- Command inventory now 100% consistent (10/10 commands with prefix)
- Templates synced (dogfooding applied)
- Installer references updated

**Before**:
- 6 commands with `aisdlc-` prefix
- 4 commands without prefix
- Inconsistent naming convention

**After**:
- 10 commands with `aisdlc-` prefix
- 0 commands without prefix
- Consistent naming convention across all commands

---

## Side Effects

**Positive**:
- Improved consistency and discoverability
- Clear framework command identification
- Better user experience (predictable naming)

**Breaking Changes**:
- Users must use new command names: `/aisdlc-apply-persona` vs `/apply-persona`
- Old command names no longer work
- Migration note: Rename commands in any scripts/documentation

---

## Future Considerations

1. Update example projects with renamed commands (via `/aisdlc-release`)
2. Create migration guide if users have old command references
3. Consider adding command aliases for backward compatibility (if needed)

---

## Lessons Learned

1. **Establish naming conventions early** - Consistent prefixes prevent confusion
2. **Use git mv for renames** - Preserves history and makes changes clear
3. **Dogfooding is critical** - Always sync templates/claude/ with main changes
4. **Dynamic installers are resilient** - setup_commands.py didn't break because it lists dynamically

---

## Traceability

**Requirements Coverage**:
- REQ-F-CMD-002: ✅ Persona management commands (renamed for consistency)

**Upstream Traceability**:
- Related to: v0.1.4 implicit session model release
- Part of: Command system consistency improvements

**Downstream Traceability**:
- Commit: TBD (checkpoint in progress)
- Release: v0.1.4+ (post-release improvement)

---

## Metrics

- **Files Renamed**: 8 (4 main + 4 templates)
- **Files Modified**: 1 (installers/setup_commands.py)
- **Lines Changed in Commands**: ~20 (cross-references)
- **Commands with aisdlc- prefix**: 6 → 10 (+67% consistency)

---

## Related

- **Part of**: REQ-F-CMD-002 (Persona Management)
- **Follows**: v0.1.4 release (implicit session model)
- **Blocked**: Task #3 (Command System Documentation) until commands finalized
- **References**: Command naming convention established in v0.1.4
