# TCS-006: /aisdlc-release Command

**Status**: ✅ Implemented
**Date**: 2025-11-27
**Requirements**: REQ-F-CMD-003
**ADR Reference**: [ADR-002](../adrs/ADR-002-commands-for-workflow-integration.md)
**Implementation**: `claude-code/plugins/aisdlc-methodology/commands/aisdlc-release.md`

---

## Purpose

Validate that the `/aisdlc-release` command correctly creates project releases with version bumping, changelog generation, and git tag creation.

---

## Preconditions

- Git repository initialized
- At least one commit exists
- Preferably on main branch (warning if not)

---

## Test Scenarios

| ID | Scenario | Input State | Expected Output | Priority |
|----|----------|-------------|-----------------|----------|
| RL-001 | Clean state | No uncommitted changes, on main | Release created, tag incremented | High |
| RL-002 | Uncommitted changes | Modified files not committed | Error: "Uncommitted changes detected" | High |
| RL-003 | Not on main | On feature branch | Warning: "Not on main branch" | Medium |
| RL-004 | First release | No existing tags | Creates v0.0.1 | High |
| RL-005 | Build bump | v0.4.0 exists | Creates v0.4.1 | High |
| RL-006 | Dry run | --dry-run flag | Shows what would happen, no changes | Medium |
| RL-007 | No commits since tag | Tag is HEAD | Warning: "No changes since last release" | Low |

---

## Validation Criteria

- [ ] Pre-release checks executed (git status, branch check)
- [ ] Version correctly incremented (patch/build number only)
- [ ] Changelog generated from commits since last tag
- [ ] Annotated git tag created locally
- [ ] Next steps provided (push instructions)
- [ ] No automatic push to remote (safety)
- [ ] Dry-run mode available for preview

---

## Version Format

```
v{MAJOR}.{MINOR}.{PATCH}

Automatic: v0.4.0 → v0.4.1 (patch bump)
Manual: Major/minor bumps require manual tag
```

---

## Expected Output Format

```
╔══════════════════════════════════════════════════════════════╗
║              Project Release Complete                        ║
╚══════════════════════════════════════════════════════════════╝

📦 Previous Version: v0.4.0
🆕 New Version: v0.4.1 (build bump)
🏷️  Tag Created: v0.4.1
⏱️  Timestamp: 2025-11-27

📝 Included Changes:
   - feat: Add new feature
   - fix: Fix bug

📝 Next Steps:
   1. Review tag: git show v0.4.1
   2. Push tag: git push origin v0.4.1
   3. Push commits: git push origin main
   4. Create GitHub release (optional)
```

---

## Test Implementation

**File**: `claude-code/tests/commands/test_commands.py`
**Class**: `TestReleaseCommand`
**Tests**: 4

```python
class TestReleaseCommand:
    def test_release_detects_uncommitted_changes(self, temp_project):
        """RL-002: Release detects uncommitted changes."""

    def test_release_detects_branch(self, temp_project):
        """RL-003: Release detects current branch."""

    def test_release_version_increment(self):
        """RL-005: Version correctly incremented."""

    def test_release_creates_tag(self, temp_project):
        """RL-001: Release creates annotated tag."""
```

---

## Requirement Traceability

| Requirement | How Validated |
|-------------|---------------|
| REQ-F-CMD-003 | Release management command works correctly |

---

## Safety Features

1. **Uncommitted changes detection** - Blocks release if dirty
2. **Branch verification** - Warns if not on main
3. **Dry-run mode** - Preview without changes
4. **No automatic push** - User must explicitly push
5. **Rollback** - Easy to delete local tag if error

---

## Notes

- This command only does patch/build bumps (x.y.z → x.y.z+1)
- For major/minor version changes, manually create the tag
- Tag message includes changelog from commits
