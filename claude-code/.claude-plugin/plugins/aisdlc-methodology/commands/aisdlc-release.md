# /aisdlc-release - Commit, Tag, and Push Release

Create a new release: commit any changes, bump version, create tag, push everything.

<!-- Implements: REQ-TOOL-003 (Workflow Commands) -->
<!-- Implements: REQ-TOOL-005 (Release Management) -->

**Usage**: `/aisdlc-release` or `/aisdlc-release "optional commit message"`

## What It Does

1. **Commit** any uncommitted changes (like `/aisdlc-commit`)
2. **Bump** version (patch: x.y.z → x.y.z+1)
3. **Tag** with changelog
4. **Push** commits and tag

## Instructions

### Step 1: Check for Changes and Commit

```bash
# Check for uncommitted changes
git status --short
```

**If changes exist**:
- Generate commit message from diff (or use provided message)
- Show message and ask for confirmation
- Commit: `git add -A && git commit -m "{message}"`

**If no changes**:
- Continue to tagging (release existing commits)

### Step 2: Calculate Next Version

```bash
# Get current version
CURRENT_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")

# Bump patch version
# v0.5.1 → v0.5.2
```

### Step 3: Generate Changelog

```bash
# Get commits since last tag
git log $CURRENT_VERSION..HEAD --pretty=format:"- %s" --no-merges
```

### Step 4: Create Tag and Push

```bash
# Create annotated tag
git tag -a "$NEW_VERSION" -m "Release $NEW_VERSION

Changes:
{changelog}

🤖 Generated with [Claude Code](https://claude.com/claude-code)"

# Push everything
git push origin main
git push origin $NEW_VERSION
```

### Step 5: Report

```
╔══════════════════════════════════════════════════════════════╗
║                    Release Complete                          ║
╚══════════════════════════════════════════════════════════════╝

📦 Previous: {old_version}
🆕 Released: {new_version}

📝 Changes:
   - commit 1
   - commit 2
   - commit 3

✅ Pushed: commits + tag

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Optional: Create GitHub release
  gh release create {new_version} --generate-notes
```

## Examples

```
> /aisdlc-release

📦 Current Version: v0.5.1

📝 Uncommitted changes:
   M  commands/aisdlc-help.md
   M  plugin.json

Commit message:
─────────────────────────
refactor: Remove finish-task command

🤖 Generated with Claude Code
─────────────────────────

Proceed with release? [Y/n] y

✅ Committed: 24f790f
🆕 New Version: v0.5.2
🏷️  Tagged: v0.5.2
📤 Pushed: commits + tag

╔══════════════════════════════════════════════════════════════╗
║                    Release Complete                          ║
╚══════════════════════════════════════════════════════════════╝
```

```
> /aisdlc-release "big refactor done"

(uses provided message, same flow)
```

## Version Bump

Default: **patch** bump (x.y.z → x.y.z+1)

For major/minor bumps, specify manually:
```
/aisdlc-release --minor    # x.y.z → x.y+1.0
/aisdlc-release --major    # x.y.z → x+1.0.0
```

---

**Note**: This is `/aisdlc-commit` + version bump + tag + push. Use for releases.
