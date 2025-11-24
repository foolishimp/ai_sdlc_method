# Task: Root Folder Cleanup and Guide Updates

**Status**: Completed
**Date**: 2025-11-25
**Time**: 03:01
**Actual Time**: 1.5 hours

**Task ID**: Impromptu (not pre-planned)
**Requirements**: REQ-NFR-DOC-001 (Documentation organization)

---

## Problem

After the MVP baseline cleanup (Task #5), the root folder had 9 markdown files which made it cluttered and difficult to navigate. Additionally, three key guide files (JOURNEY.md, QUICKSTART.md, NEW_PROJECT_SETUP.md) needed review and updates to:
1. Remove MCP service references (de-scoped in MVP)
2. Define clear purposes for each guide
3. Ensure proper cross-referencing between guides

---

## Investigation

### Current State Analysis
1. **Root folder had 9 markdown files** (too cluttered)
2. **MCP service references** still present in INTENT.md, INVENTORY.md, README.md
3. **Three guide files** lacked clear differentiation and cross-references
4. **JOURNEY.md** was in `docs/` but should be with other guides

### Findings
- QUICKSTART.md (477 lines) - Should focus on 5-10 min quick start
- NEW_PROJECT_SETUP.md (875 lines) - Should be detailed setup guide
- JOURNEY.md (1760 lines) - Should be complete 7-stage walkthrough
- All three had overlapping content and unclear purposes

---

## Solution

### Phase 1: Root Folder Reorganization
Created new directory structure:
- `docs/info/` - Reference information (INVENTORY, SKILLS_INVENTORY, AGENTS_VS_SKILLS)
- `docs/guides/` - How-to guides (JOURNEY, NEW_PROJECT_SETUP, PLUGIN_GUIDE)
- `docs/requirements/` - Requirements and intent (INTENT.md moved here)

**Moved files**:
- AGENTS_VS_SKILLS.md → docs/info/
- INVENTORY.md → docs/info/
- SKILLS_INVENTORY.md → docs/info/
- INTENT.md → docs/requirements/ (root of requirements)
- NEW_PROJECT_SETUP.md → docs/guides/
- PLUGIN_GUIDE.md → docs/guides/
- JOURNEY.md → docs/guides/ (from docs/)

**Root folder reduced to 3 essential files**:
- README.md (main entry point)
- CLAUDE.md (Claude Code auto-reads this)
- QUICKSTART.md (quick start guide)

### Phase 2: Remove MCP Service References
Updated files to remove MCP service references (de-scoped in MVP):
- **README.md**: Removed "Added MCP service integration plan" from v2.0.0 history
- **INTENT.md**: Removed 10+ MCP references, updated scope to focus on Claude Code
- **INVENTORY.md**: Removed MCP service dependencies section and testing checklist item

### Phase 3: Update Guide Files

**QUICKSTART.md** (477 lines):
- **Purpose**: Get started in 5-10 minutes
- **Changes**:
  - Added clear "Choose your path" navigation at top
  - Simplified to plugin installation + quick example
  - Removed "Method 2: Direct Python Usage" (not MVP)
  - Added cross-references to JOURNEY and NEW_PROJECT_SETUP
  - Updated "Next Steps" section with progressive learning path

**NEW_PROJECT_SETUP.md** (875 lines):
- **Purpose**: Complete project setup guide (30-45 min)
- **Changes**:
  - Updated header with clear purpose and audience
  - Simplified Step 1 to use `/plugin install` (MVP approach)
  - Made Python installer tools optional (advanced users)
  - Added "Next Steps" section pointing to JOURNEY.md
  - Updated "Getting Help" with correct paths
  - Added cross-references to QUICKSTART and JOURNEY

**JOURNEY.md** (1760 lines):
- **Purpose**: Complete 7-stage walkthrough (2-3 hours)
- **Changes**:
  - Moved from `docs/` to `docs/guides/` (better organization)
  - Updated header with cross-references to QUICKSTART and NEW_PROJECT_SETUP
  - Fixed "Deep Dive Resources" section with correct paths
  - Updated all internal paths after reorganization
  - Added clear progressive learning path references

### Phase 4: Update Cross-References
Updated all cross-references across files:
- CLAUDE.md: Updated PLUGIN_GUIDE.md path (2 locations)
- QUICKSTART.md: Updated INVENTORY, NEW_PROJECT_SETUP, PLUGIN_GUIDE paths (4 locations)
- README.md: Updated JOURNEY.md path, added new "Reference" section

---

## Files Modified

### Moved (6 files):
- `AGENTS_VS_SKILLS.md` → `docs/info/AGENTS_VS_SKILLS.md`
- `INVENTORY.md` → `docs/info/INVENTORY.md`
- `SKILLS_INVENTORY.md` → `docs/info/SKILLS_INVENTORY.md`
- `INTENT.md` → `docs/requirements/INTENT.md` (user moved to requirements)
- `NEW_PROJECT_SETUP.md` → `docs/guides/NEW_PROJECT_SETUP.md`
- `PLUGIN_GUIDE.md` → `docs/guides/PLUGIN_GUIDE.md`
- `docs/JOURNEY.md` → `docs/guides/JOURNEY.md`

### Modified (7 files):
- `CLAUDE.md` - Updated 2 PLUGIN_GUIDE.md references
- `QUICKSTART.md` - Major restructure (96 line changes)
- `README.md` - Updated JOURNEY.md path, added Reference section (13 line changes)
- `docs/guides/JOURNEY.md` - Updated cross-references (27 line changes)
- `docs/guides/NEW_PROJECT_SETUP.md` - Major updates (83 line changes)
- `docs/info/INTENT.md` - Removed MCP references (336 line deletions)
- `docs/info/INVENTORY.md` - Removed MCP section (7 line deletions)

### Created:
- `docs/info/` directory
- `docs/guides/` directory

---

## Result

✅ **Task completed successfully**

### Root Folder Organization
- **Before**: 9 markdown files (cluttered)
- **After**: 3 essential files (clean)
- **New structure**:
  - `docs/info/` - Reference information
  - `docs/guides/` - How-to guides
  - Root - Only essentials

### MCP Service Cleanup
- ✅ Removed all MCP service references from root *.md files
- ✅ Updated INTENT.md scope to MVP baseline (Claude Code native)
- ✅ Cleaned INVENTORY.md dependencies section
- ✅ Updated README.md version history

### Guide File Updates
- ✅ **QUICKSTART.md**: Focused on 5-10 min quick start
- ✅ **NEW_PROJECT_SETUP.md**: Detailed 30-45 min setup guide
- ✅ **JOURNEY.md**: Complete 2-3 hour walkthrough
- ✅ All three files cross-reference each other properly
- ✅ Clear progressive learning path established

### Documentation Quality
- Improved navigation between guides
- Clear purpose for each guide
- Proper cross-referencing
- Logical directory structure

---

## Side Effects

**Positive**:
- Much cleaner root folder (9 → 3 files)
- Clear documentation hierarchy
- Easy to find relevant guides
- Better onboarding experience (progressive learning)
- All MCP references removed (consistent with MVP scope)

**Considerations**:
- Any external links to old paths will break (need update)
- Users with bookmarks may need to update them
- Git history shows files as moved (may need `git log --follow`)

---

## Future Considerations

1. **Create docs/README.md** if it doesn't exist to explain the new structure
2. **Update any external documentation** that links to moved files
3. **Consider adding a CONTRIBUTING.md** to explain where to put new docs
4. **Review examples/** folder for similar cleanup opportunities

---

## Lessons Learned

1. **Fewer files in root = better UX** - Only keep essential starter files in root
2. **Clear file purposes matter** - Three guides now have distinct purposes and audiences
3. **Cross-referencing is critical** - Users need clear paths between related docs
4. **Progressive learning paths work** - QUICKSTART → NEW_PROJECT_SETUP → JOURNEY
5. **Cleanup after scope changes is essential** - Removed stale MCP references

---

## Traceability

**Requirements Coverage**:
- REQ-NFR-DOC-001: Documentation organization ✅

**Upstream Traceability**:
- Related to Task #5: Validate Implementation - MVP Baseline
- Addresses MCP service de-scoping
- Supports v0.1.0 MVP baseline

**Downstream Traceability**:
- Files moved with git mv (preserves history)
- Cross-references updated throughout codebase
- Ready for commit

---

## Metrics

- **Files Moved**: 7
- **Directories Created**: 2
- **Lines Removed**: 440 (mostly MCP references)
- **Lines Modified**: 126 (cross-references + content updates)
- **Root Files**: 9 → 3 (67% reduction)
- **Documentation Structure**: Significantly improved

---

## Related

- **Follows**: Task #5 - Validate Implementation - MVP Baseline
- **Addresses**: MCP service removal, documentation cleanup
- **Improves**: User onboarding experience
- **Establishes**: Progressive learning path (QUICKSTART → SETUP → JOURNEY)
