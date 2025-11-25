# /aisdlc-release - Project Release Management

Create a new release of your project by bumping the build number, generating changelog, and creating a git tag.

<!-- Implements: REQ-F-CMD-003 (Release Management Command) -->

## Command Purpose

Execute controlled release of your project:
1. Validate release readiness (clean git state, on main branch)
2. Automatically bump build number (x.y.z → x.y.z+1)
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

### 2. Calculate Next Build Number

Automatically increment the build number (patch version):

```bash
# Parse current version (e.g., v0.2.0 → major=0, minor=2, build=0)
VERSION="${CURRENT_VERSION#v}"
MAJOR=$(echo "$VERSION" | cut -d. -f1)
MINOR=$(echo "$VERSION" | cut -d. -f2)
BUILD=$(echo "$VERSION" | cut -d. -f3)

# Increment build number
NEW_BUILD=$((BUILD + 1))
NEW_VERSION="v${MAJOR}.${MINOR}.${NEW_BUILD}"

echo "🆕 New Version: $NEW_VERSION (build bump)"
```

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

### 4. Create Git Tag

```bash
# Create annotated tag
NEW_VERSION="vX.Y.Z"  # calculated from step 2
TAG_MESSAGE="Release $NEW_VERSION

Changes:
$(git log $CURRENT_VERSION..HEAD --pretty=format:"- %s" --no-merges)

🤖 Generated with [Claude Code](https://claude.com/claude-code)"

git tag -a "$NEW_VERSION" -m "$TAG_MESSAGE"

echo "🏷️  Created tag: $NEW_VERSION"
```

### 5. Generate Release Report

```bash
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              Project Release Complete                        ║"
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
# Standard release (auto-bumps build number)
/aisdlc-release

# Dry run (preview without changes)
/aisdlc-release --dry-run

# Skip changelog display
/aisdlc-release --no-changelog
```

**Note**: This command only bumps the build number (e.g., v0.2.0 → v0.2.1). For major/minor version changes, manually create the tag: `git tag -a v0.3.0 -m "Release v0.3.0"`

## Example Session

**User**: `/aisdlc-release`

**Claude**:
```
╔══════════════════════════════════════════════════════════════╗
║              Project Release                                 ║
╚══════════════════════════════════════════════════════════════╝

📦 Current Version: v0.1.4

✅ Pre-release Checks:
   - No uncommitted changes ✅
   - On main branch ✅

🆕 New Version: v0.1.5 (build bump)

📝 Changes since v0.1.4:
   - feat: Add new feature X
   - fix: Fix bug in Y
   - docs: Update documentation

Creating release...
   ✅ Tag created: v0.1.5
   ✅ Release notes generated

╔══════════════════════════════════════════════════════════════╗
║              Project Release Complete                        ║
╚══════════════════════════════════════════════════════════════╝

📦 Previous Version: v0.1.4
🆕 New Version: v0.1.5
⏱️  Timestamp: 2025-11-25 14:00:00

📝 Next Steps:
   1. Review tag: git show v0.1.5
   2. Push tag: git push origin v0.1.5
   3. Create GitHub release (optional)
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
git tag -d vX.Y.Z  # Delete local tag
```

## Integration with GitHub

After local release, optionally create GitHub release:

```bash
# Create GitHub release with auto-generated notes
gh release create vX.Y.Z --generate-notes

# Or with custom notes
gh release create vX.Y.Z --title "vX.Y.Z" --notes "Release notes here"
```

---

**Usage**: Run `/aisdlc-release` to create a new project release.
