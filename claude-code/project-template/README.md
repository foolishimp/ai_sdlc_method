# Claude Templates

This directory contains **template files** that are copied to target projects by the Python installers.

## Purpose

These templates serve as the **source of truth** for all AI SDLC Method installations. When you run the installers in `../../installers/`, they copy these templates to target projects.

## Structure

```
templates/claude/
├── .ai-workspace/           # Developer workspace template
│   ├── config/
│   │   └── workspace_config.yml
│   ├── tasks/
│   │   ├── todo/
│   │   │   └── TODO_LIST.md
│   │   ├── active/
│   │   │   └── ACTIVE_TASKS.md
│   │   ├── finished/
│   │   └── archive/
│   ├── session/
│   └── templates/
│       ├── TASK_TEMPLATE.md
│       ├── FINISHED_TASK_TEMPLATE.md
│       ├── SESSION_TEMPLATE.md
│       ├── SESSION_STARTER.md
│       └── PAIR_PROGRAMMING_GUIDE.md
│
├── .claude/                 # Claude commands template
│   └── commands/
│       ├── todo.md
│       ├── start-session.md
│       ├── finish-task.md
│       ├── commit-task.md
│       ├── apply-persona.md
│       ├── switch-context.md
│       ├── load-context.md
│       ├── current-context.md
│       └── ... (more commands)
│
├── CLAUDE.md.template       # Project guidance template
└── README.md                # This file
```

## Templates Explained

### `.ai-workspace/` Template

The **Developer Workspace** template provides:

**Task Management:**
- `tasks/todo/TODO_LIST.md` - Quick capture template
- `tasks/active/ACTIVE_TASKS.md` - Formal tasks template
- `tasks/finished/` - Directory for completed task docs
- `tasks/archive/` - Directory for old tasks

**Session Management:**
- `session/current_session.md` - Active session template (git-ignored in target)
- `session/history/` - Past sessions (git-ignored in target)

**Templates:**
- `templates/TASK_TEMPLATE.md` - Template for creating tasks
- `templates/FINISHED_TASK_TEMPLATE.md` - Template for task completion docs
- `templates/SESSION_TEMPLATE.md` - Template for sessions
- `templates/SESSION_STARTER.md` - Session startup checklist
- `templates/PAIR_PROGRAMMING_GUIDE.md` - Human-AI collaboration guide

**Configuration:**
- `config/workspace_config.yml` - Workspace settings

### `.claude/` Template

The **Claude Commands** template provides slash commands:

**Task Commands:**
- `/todo` - Quick task capture
- `/finish-task` - Complete task with documentation
- `/commit-task` - Generate commit message

**Session Commands:**
- `/start-session` - Begin development session with checklist

**Context Commands:**
- `/apply-persona` - Apply development persona
- `/switch-context` - Switch project context
- `/load-context` - Load context from file
- `/current-context` - Show current context

**Project Commands:**
- `/list-projects` - List available projects
- `/list-personas` - List available personas
- `/persona-checklist` - Show persona checklist
- `/show-full-context` - Display complete context

### `CLAUDE.md.template`

The **project guidance template** that gets copied as `CLAUDE.md` to target projects.

Contains:
- Quick start instructions
- Directory structure overview
- Key principles
- Development workflow
- Available commands
- TDD process
- Resources and links
- Placeholder sections for project-specific customization

## Using These Templates

### For Installers

The Python installers in `../../installers/` automatically copy these templates:

```python
# In setup_workspace.py
self.workspace_source = self.templates_root / ".ai-workspace"
self.copy_directory(self.workspace_source, target / ".ai-workspace")

# In setup_commands.py
self.commands_source = self.templates_root / ".claude"
self.copy_directory(self.commands_source, target / ".claude")

# In setup_all.py
self.copy_file(
    self.templates_root / "CLAUDE.md.template",
    target / "CLAUDE.md"
)
```

### Manual Installation

You can also manually copy these templates:

```bash
# Copy workspace
cp -r templates/claude/.ai-workspace /my/project/

# Copy commands
cp -r templates/claude/.claude /my/project/

# Copy CLAUDE.md
cp templates/claude/CLAUDE.md.template /my/project/CLAUDE.md
```

## Customizing Templates

### For ai_sdlc_method Project

To customize templates for **all future installations**:

1. Edit files in this `templates/claude/` directory
2. Test with installer:
   ```bash
   cd ../../installers
   python setup_all.py --target /test/project --force
   ```
3. Verify templates were copied correctly
4. Commit changes to templates

### For Target Projects

After installation, target projects should customize:

1. **CLAUDE.md** - Add project-specific sections:
   - Technology stack
   - Project structure
   - Development commands
   - Team conventions
   - Domain knowledge

2. **workspace_config.yml** - Adjust settings:
   - Task tracking preferences
   - Session check-in frequency
   - TDD enforcement
   - Test coverage thresholds

3. **Task templates** - Modify if needed:
   - Add custom acceptance criteria
   - Include project-specific checklists
   - Add domain-specific sections

## Template Versioning

Templates should be versioned with the AI SDLC Method:

- **Version**: 1.0
- **Last Updated**: 2025-01-21
- **Compatibility**: Claude Code 1.0+

When updating templates:
1. Update version in comments
2. Document changes in CHANGELOG
3. Update installer scripts if structure changes
4. Test with all installer combinations

## Best Practices

### Maintaining Templates

**DO:**
- ✅ Keep templates generic and reusable
- ✅ Use placeholders like `[TODO]`, `[PROJECT_NAME]`
- ✅ Document template structure clearly
- ✅ Test templates with installers regularly
- ✅ Version control all template changes

**DON'T:**
- ❌ Include project-specific content
- ❌ Hardcode paths or URLs
- ❌ Add large binary files
- ❌ Break installer compatibility

### Template Updates

When updating templates:

```bash
# 1. Make changes to templates
vim templates/claude/.ai-workspace/templates/TASK_TEMPLATE.md

# 2. Test installation
cd installers
python setup_all.py --target /tmp/test --force

# 3. Verify copied correctly
ls -la /tmp/test/.ai-workspace/templates/
cat /tmp/test/.ai-workspace/templates/TASK_TEMPLATE.md

# 4. Clean up test
rm -rf /tmp/test

# 5. Commit template changes
git add templates/claude/
git commit -m "Update task template with new section"
```

## Relationship to ai_sdlc_method Project

**Important:** The ai_sdlc_method repository is **both**:

1. **A working project** - Has its own `.ai-workspace/` and `.claude/` for development
2. **A template source** - Provides `templates/claude/` for other projects

```
ai_sdlc_method/
├── .ai-workspace/           # THIS project's workspace (for ai_sdlc_method dev)
├── .claude/                 # THIS project's commands (for ai_sdlc_method dev)
├── templates/
│   └── claude/
│       ├── .ai-workspace/   # TEMPLATE for other projects
│       └── .claude/         # TEMPLATE for other projects
└── installers/              # Scripts to deploy templates
```

### Keeping in Sync

To keep templates synchronized with this project's files:

```bash
# Update templates from this project's workspace
cp -r .ai-workspace/* templates/claude/.ai-workspace/
cp -r .claude/* templates/claude/.claude/

# Or vice versa (update project from templates)
cp -r templates/claude/.ai-workspace/* .ai-workspace/
cp -r templates/claude/.claude/* .claude/
```

**Note:** Be careful not to copy local session data or project-specific customizations.

## Examples

### Example 1: Adding a New Command Template

```bash
# 1. Create new command in .claude/commands/
cat > .claude/commands/my-command.md <<'EOF'
# My New Command

Description of what this command does.

Instructions for Claude...
EOF

# 2. Copy to templates
cp .claude/commands/my-command.md templates/claude/.claude/commands/

# 3. Test installation
cd installers
python setup_commands.py --target /tmp/test --force

# 4. Verify
ls /tmp/test/.claude/commands/my-command.md
```

### Example 2: Updating Task Template

```bash
# 1. Edit template
vim templates/claude/.ai-workspace/templates/TASK_TEMPLATE.md

# 2. Test full installation
cd installers
python setup_all.py --target /tmp/test --force

# 3. Verify template was copied
cat /tmp/test/.ai-workspace/templates/TASK_TEMPLATE.md

# 4. Test creating a task using template in target
cd /tmp/test
# ... test task creation workflow ...

# 5. Clean up
rm -rf /tmp/test
```

### Example 3: Customizing for Enterprise

```bash
# Create enterprise variant
cp -r templates/claude templates/claude-enterprise

# Customize for enterprise
# - Add compliance checklists
# - Include security requirements
# - Add enterprise-specific commands

# Create custom installer for enterprise variant
# (would need to modify installer to use enterprise templates)
```

## Support

- **Template Issues**: https://github.com/foolishimp/ai_sdlc_method/issues
- **Installation Help**: See `../../installers/README.md`
- **Documentation**: `../../docs/`

---

## Version

**Templates Version**: 1.0
**AI SDLC Method**: 1.0
**Last Updated**: 2025-01-21

---

*These templates power AI-augmented development across all projects!* 🚀
