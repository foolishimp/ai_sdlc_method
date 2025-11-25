# /aisdlc-release - Framework Release Management

Create a new release of the ai_sdlc_method framework with version management, changelog generation, and git tagging.

<!-- Implements: REQ-F-CMD-003 (Release Management Command) -->

## Command Purpose

Execute controlled release of the ai_sdlc_method framework:
1. Validate release readiness (clean git state, on main branch)
2. Determine version bump (major/minor/patch)
3. Generate changelog from git commits
4. Create annotated git tag
5. Generate release summary with next steps

## Implementation Steps

### 1. Pre-release Validation

```bash
# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ Error: Uncommitted changes detected"
    echo "   Please commit or stash changes before release"
    git status --short
    exit 1
fi

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "⚠️  Warning: Not on main branch (current: $CURRENT_BRANCH)"
    echo "   Releases should typically be from main"
fi

# Get current version
CURRENT_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
echo "📦 Current Version: $CURRENT_VERSION"
```

### 2. Version Bump Selection

Ask user for version bump type:

```
Options:
1. patch (v0.1.4 → v0.1.5) - Bug fixes, minor updates
2. minor (v0.1.4 → v0.2.0) - New features, backwards compatible
3. major (v0.1.4 → v1.0.0) - Breaking changes
4. custom - Specify exact version
```

Parse current version and calculate new version based on selection.

### 3. Changelog Generation

```bash
# Get commits since last tag
echo ""
echo "📝 Changes since $CURRENT_VERSION:"
echo ""

git log $CURRENT_VERSION..HEAD --pretty=format:"- %s" --no-merges | while read line; do
    echo "   $line"
done

echo ""
```

### 4. Version Update (if applicable)

Update version references in:
- `marketplace.json` (version field)
- Plugin `plugin.json` files (if version changed)

### 5. Create Git Tag

```bash
# Create annotated tag
NEW_VERSION="v0.2.0"  # calculated from step 2
TAG_MESSAGE="Release $NEW_VERSION

Changes:
$(git log $CURRENT_VERSION..HEAD --pretty=format:"- %s" --no-merges)

🤖 Generated with [Claude Code](https://claude.com/claude-code)"

git tag -a "$NEW_VERSION" -m "$TAG_MESSAGE"

echo "🏷️  Created tag: $NEW_VERSION"
```

### 6. Generate Release Report

```bash
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           AI SDLC Method Release Complete                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📦 Previous Version: $CURRENT_VERSION"
echo "🆕 New Version: $NEW_VERSION"
echo "🏷️  Tag Created: $NEW_VERSION"
echo "⏱️  Timestamp: $(date)"
echo ""
echo "📝 Included Changes:"
git log $CURRENT_VERSION..HEAD --pretty=format:"   - %s" --no-merges
echo ""
echo ""
echo "📝 Next Steps:"
echo "   1. Review tag: git show $NEW_VERSION"
echo "   2. Push tag: git push origin $NEW_VERSION"
echo "   3. Push commits: git push origin main"
echo "   4. Create GitHub release (optional):"
echo "      gh release create $NEW_VERSION --title \"$NEW_VERSION\" --notes-file -"
echo ""
```

## Command Options

```bash
# Standard release (prompts for version bump)
/aisdlc-release

# Dry run (preview without changes)
/aisdlc-release --dry-run

# Specify version explicitly
/aisdlc-release --version v0.2.0

# Skip changelog display
/aisdlc-release --no-changelog

# Force release even with uncommitted changes (not recommended)
/aisdlc-release --force
```

## Example Session

**User**: `/aisdlc-release`

**Claude**:
```
╔══════════════════════════════════════════════════════════════╗
║           AI SDLC Method Release                             ║
╚══════════════════════════════════════════════════════════════╝

📦 Current Version: v0.1.4

✅ Pre-release Checks:
   - No uncommitted changes ✅
   - On main branch ✅
   - Tests passing ✅

📝 Changes since v0.1.4:
   - feat: Add release target tracking to requirements
   - feat: Repurpose release command for framework releases
   - refactor: Move examples to separate repo
   - docs: Update traceability matrix with release column

🔢 Select version bump:
   1. patch (v0.1.4 → v0.1.5)
   2. minor (v0.1.4 → v0.2.0)
   3. major (v0.1.4 → v1.0.0)
   4. custom

> User selects: 2 (minor)

🆕 New Version: v0.2.0

Creating release...
   ✅ Tag created: v0.2.0
   ✅ Release notes generated

╔══════════════════════════════════════════════════════════════╗
║           AI SDLC Method Release Complete                    ║
╚══════════════════════════════════════════════════════════════╝

📦 Previous Version: v0.1.4
🆕 New Version: v0.2.0
⏱️  Timestamp: 2025-11-25 13:45:00

📝 Next Steps:
   1. Review tag: git show v0.2.0
   2. Push tag: git push origin v0.2.0
   3. Push commits: git push origin main
   4. Create GitHub release (optional)
```

## Version Bump Rules

Follow Semantic Versioning (SemVer):

| Change Type | Bump | Example |
|-------------|------|---------|
| Bug fixes, typos, minor docs | patch | v0.1.4 → v0.1.5 |
| New features, backwards compatible | minor | v0.1.4 → v0.2.0 |
| Breaking changes, major rewrites | major | v0.1.4 → v1.0.0 |

## Safety Features

**Pre-release Checks**:
- Uncommitted changes detection
- Branch verification (warns if not on main)
- Dry-run mode for preview

**No Automatic Push**:
- Tags are created locally only
- User must explicitly push tag and commits
- Allows review before publishing

**Rollback**:
```bash
# If tag created in error
git tag -d v0.2.0  # Delete local tag
```

## Integration with GitHub

After local release, optionally create GitHub release:

```bash
# Create GitHub release with auto-generated notes
gh release create v0.2.0 --generate-notes

# Or with custom notes
gh release create v0.2.0 --title "v0.2.0 - Release Management" --notes "
## What's New
- Release management command
- Release target tracking
- Examples moved to separate repo

## Full Changelog
See git log for details.
"
```

## Traceability

This command implements **REQ-F-CMD-003** (Release Management Command).

**Upstream**: INT-AISDLC-001 Section 3.1 (Workflow automation)
**Design**: Pending design documentation
**Tests**: Pending

---

**Usage**: Run `/aisdlc-release` to create a new framework release.
