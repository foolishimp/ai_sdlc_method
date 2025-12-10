# /aisdlc-commit - Commit Current State

Commit all current changes with an auto-generated message based on context.

<!-- Implements: REQ-TOOL-003 (Workflow Commands) -->

**Usage**: `/aisdlc-commit` or `/aisdlc-commit "optional message"`

**Instructions**:

1. **Check git status**
   ```bash
   git status --short
   git diff --stat
   ```

2. **If no changes**, report "Nothing to commit" and exit

3. **Gather context** (if available):
   - Read `.ai-workspace/tasks/active/ACTIVE_TASKS.md` for in-progress tasks
   - Check recent conversation for what was worked on
   - Look for REQ-* tags in changed files

4. **Generate commit message**:
   - Summarize what changed based on diff
   - Include REQ-* tags if found in changes
   - Keep it concise (1-2 sentences)

   Format:
   ```
   {type}: {brief description}

   {optional: bullet points of key changes}

   {Implements: REQ-* if applicable}

   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude <noreply@anthropic.com>
   ```

   Types: feat, fix, docs, refactor, test, chore

5. **Show commit message** and ask user to confirm or edit

6. **If confirmed**, commit and push:
   ```bash
   git add -A
   git commit -m "{message}"
   git push
   ```

7. **Report result**:
   ```
   ✅ Committed and pushed: {short_hash}

   {commit message summary}
   ```

**Examples**:

```
> /aisdlc-commit

Proposed commit message:
─────────────────────────
fix: Update installer to clear plugin cache correctly

- Fixed cache path from /cache/ to /marketplaces/
- Added troubleshooting docs to help and installer

🤖 Generated with Claude Code
─────────────────────────

Commit and push? [Y/n]
```

```
> /aisdlc-commit "WIP: auth feature"

✅ Committed and pushed: a1b2c3d

WIP: auth feature
```

---

**Note**: Use `/aisdlc-release` when you want to commit + tag a new version.
