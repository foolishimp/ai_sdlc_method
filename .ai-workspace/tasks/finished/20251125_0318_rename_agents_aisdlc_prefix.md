# Task #8: Rename Agents with aisdlc- Prefix for Namespace Safety

**Status**: Completed
**Date**: 2025-11-25
**Time**: 03:18
**Actual Time**: 15 minutes (Estimated: 1 hour)

**Task ID**: #8
**Requirements**: REQ-F-PLUGIN-001 (Plugin System with Marketplace Support - namespace safety)

---

## Problem

Agent files had generic names (requirements-agent.md, code-agent.md, etc.) which could conflict with other agent systems or methodologies in a multi-agent environment. This created namespace collision risks when users load multiple methodology plugins.

---

## Investigation

### Current State Analysis
1. **7 agent files** with generic names in 3 locations:
   - `.claude/agents/` (project level)
   - `templates/claude/.claude/agents/` (templates)
   - `examples/local_projects/data_mapper.test02/.claude/agents/` (example)

2. **Inconsistency** with command naming:
   - Commands: `aisdlc-status`, `aisdlc-checkpoint-tasks` ✅
   - Agents: `requirements-agent`, `code-agent` ❌

3. **Risk**: Users loading multiple methodologies could have name conflicts

### Findings
- Total agent files: 21 (7 main + 7 templates + 7 example)
- Documentation references: 30+ locations
- Naming convention needed for consistency

---

## Solution

### Phase 1: Rename Agent Files
Renamed all 21 agent files with `aisdlc-` prefix:

**Main agents** (.claude/agents/):
- requirements-agent.md → aisdlc-requirements-agent.md
- design-agent.md → aisdlc-design-agent.md
- tasks-agent.md → aisdlc-tasks-agent.md
- code-agent.md → aisdlc-code-agent.md
- system-test-agent.md → aisdlc-system-test-agent.md
- uat-agent.md → aisdlc-uat-agent.md
- runtime-feedback-agent.md → aisdlc-runtime-feedback-agent.md

**Template agents** (templates/claude/.claude/agents/):
- Same 7 renames

**Example agents** (examples/local_projects/data_mapper.test02/.claude/agents/):
- Same 7 renames

### Phase 2: Update Documentation References
Updated 30+ references across 6 files:

1. **docs/info/INVENTORY.md** - Agent template listing
2. **docs/info/AGENTS_VS_SKILLS.md** - Agent catalog
3. **docs/README.md** - 7 stage agent references
4. **docs/design/AGENTS_SKILLS_INTEROPERATION.md** - Multiple examples and diagrams
5. **docs/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md** - REQ-F-CMD-002 acceptance criteria
6. **.ai-workspace/tasks/active/ACTIVE_TASKS.md** - Task #8 description

---

## Files Modified

### Renamed (21 files):
- `.claude/agents/*-agent.md` → `aisdlc-*-agent.md` (7 files)
- `templates/claude/.claude/agents/*-agent.md` → `aisdlc-*-agent.md` (7 files)
- `examples/local_projects/data_mapper.test02/.claude/agents/*-agent.md` → `aisdlc-*-agent.md` (7 files)

### Modified (6 files):
- `docs/info/INVENTORY.md` - Updated agent listing
- `docs/info/AGENTS_VS_SKILLS.md` - Updated agent catalog
- `docs/README.md` - Updated 7 stage references
- `docs/design/AGENTS_SKILLS_INTEROPERATION.md` - Updated examples/diagrams
- `docs/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md` - Updated acceptance criteria
- `.ai-workspace/tasks/active/ACTIVE_TASKS.md` - Updated task description

---

## Result

✅ **Task completed successfully**

### Namespace Safety
- **Before**: Generic names (requirements-agent, code-agent, etc.)
- **After**: Prefixed names (aisdlc-requirements-agent, aisdlc-code-agent, etc.)
- **Benefit**: No conflicts in multi-agent environments

### Consistency
- ✅ Commands: `aisdlc-*` prefix
- ✅ Agents: `aisdlc-*` prefix
- ✅ Plugins: `@aisdlc/*` namespace
- **Result**: Consistent AISDLC namespace throughout

### Coverage
- ✅ 21 agent files renamed (100%)
- ✅ 30+ documentation references updated (100%)
- ✅ Git history preserved (used `git mv`)
- ✅ No broken links

---

## Side Effects

**Positive**:
- Consistent naming across entire AISDLC ecosystem
- No namespace conflicts with other agent systems
- Clear ownership (obviously AISDLC methodology agents)
- Easier to distinguish in multi-methodology environments

**Considerations**:
- Users with existing projects need to refresh agents
- Documentation now clearly shows aisdlc- prefix throughout
- Installer scripts already handle new names (copy from templates)

---

## Future Considerations

1. **Plugin Bundles** - Ensure bundles reference correct agent names
2. **Example Projects** - Verify all examples use new names
3. **External Documentation** - Update any external references
4. **Migration Guide** - Add note about agent rename in v0.1.x

---

## Lessons Learned

1. **Namespace prefixes critical** - Prevent conflicts early, not after issues arise
2. **Consistency matters** - All components should follow same naming pattern
3. **Git mv preserves history** - Always use git mv, not rm + add
4. **Batch renames efficient** - Chain commands with && for speed
5. **Template synchronization** - Always update templates with main files

---

## Traceability

**Requirements Coverage**:
- REQ-F-PLUGIN-001: Plugin System with Marketplace Support (namespace safety) ✅

**Upstream Traceability**:
- Addresses multi-agent environment support
- Aligns with plugin namespace (@aisdlc/*)
- Maintains consistency with command naming

**Downstream Traceability**:
- 21 files renamed with git mv (preserves history)
- 30+ documentation references updated
- Ready for installer deployment

---

## Metrics

- **Files Renamed**: 21 (7 main + 7 templates + 7 example)
- **Documentation Updates**: 6 files
- **References Updated**: 30+
- **Time Spent**: 15 minutes (vs 1 hour estimated)
- **Git History**: Preserved with git mv
- **Namespace Consistency**: 100%

---

## Related

- **Consistency**: Aligned with command naming (aisdlc-*)
- **Follows**: Plugin namespace pattern (@aisdlc/*)
- **Supports**: REQ-F-PLUGIN-001 (namespace safety)
- **Similar To**: Task #6 (persona command renames)
