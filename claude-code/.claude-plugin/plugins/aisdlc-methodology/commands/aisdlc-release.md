# /aisdlc-release - Commit, Tag, and Push Release

Create a new release: commit any changes, bump version in all files, create tag, push everything.

<!-- Implements: REQ-TOOL-003 (Workflow Commands) -->
<!-- Implements: REQ-TOOL-005 (Release Management) -->

**Usage**: `/aisdlc-release` or `/aisdlc-release "optional commit message"`

## What It Does

1. **Commit** any uncommitted changes (like `/aisdlc-commit`)
2. **Bump** version in plugin.json and stages_config.yml
3. **Commit** version bump
4. **Tag** with changelog
5. **Push** commits and tag

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
- Continue to version bump

### Step 2: Calculate Next Version

```bash
# Get current version from git tag
CURRENT_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")

# Bump patch version
# v0.5.2 → v0.5.3
```

### Step 3: Bump Version in Files

**IMPORTANT**: Update version in these files before tagging:

1. **plugin.json**: Update `"version": "X.Y.Z"` field
   - Search for: `aisdlc-methodology/.claude-plugin/plugin.json`

2. **stages_config.yml**: Update both version references
   - Search for: `aisdlc-methodology/config/stages_config.yml`
   - Update comment: `# Version: X.Y.Z`
   - Update field: `version: "X.Y.Z"`

```bash
# Commit version bump
git add -A
git commit -m "chore: Bump version to vX.Y.Z"
```

### Step 4: Generate Changelog

```bash
# Get commits since last tag
git log $CURRENT_VERSION..HEAD --pretty=format:"- %s" --no-merges
```

### Step 5: Create Tag and Push

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

### Step 6: Report

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

✅ Files Updated:
   - plugin.json
   - stages_config.yml

✅ Pushed: commits + tag

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Optional: Create GitHub release
  gh release create {new_version} --generate-notes
```

## Examples

```
> /aisdlc-release

📦 Current Version: v0.5.2

📝 Uncommitted changes:
   M  commands/aisdlc-help.md

Commit message:
─────────────────────────
fix: Update help references

🤖 Generated with Claude Code
─────────────────────────

Proceed with release? [Y/n] y

✅ Committed: a1b2c3d
📝 Bumping version: v0.5.2 → v0.5.3
   Updated: plugin.json
   Updated: stages_config.yml
✅ Committed: d4e5f6g (chore: Bump version to v0.5.3)
🏷️  Tagged: v0.5.3
📤 Pushed: commits + tag

╔══════════════════════════════════════════════════════════════╗
║                    Release Complete                          ║
╚══════════════════════════════════════════════════════════════╝
```

## Version Bump

Default: **patch** bump (x.y.z → x.y.z+1)

For major/minor bumps, specify manually:
```
/aisdlc-release --minor    # x.y.z → x.y+1.0
/aisdlc-release --major    # x.y.z → x+1.0.0
```

---

**Note**: This bumps version in plugin.json and stages_config.yml, then tags. All version sources stay in sync.
