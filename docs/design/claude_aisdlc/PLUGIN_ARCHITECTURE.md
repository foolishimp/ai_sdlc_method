# Plugin Architecture Design

**Design Document**
**Version**: 1.0
**Date**: 2025-11-23
**Status**: Draft

---

## Requirements Traceability

This design implements the following requirements:

- **REQ-F-PLUGIN-001**: Plugin system with marketplace support
- **REQ-F-PLUGIN-002**: Federated plugin loading (corporate → division → team → project)
- **REQ-F-PLUGIN-003**: Plugin bundles (startup, datascience, qa, enterprise)
- **REQ-F-PLUGIN-004**: Plugin versioning and dependency management
- **REQ-NFR-CONTEXT-001**: Persistent context across sessions
- **REQ-NFR-FEDERATE-001**: Hierarchical configuration composition

**Related Design Documents**:
- [AI SDLC UX Design](AI_SDLC_UX_DESIGN.md) - Overall user experience
- [Command System](COMMAND_SYSTEM.md) - Slash commands integration

---

## 1. Overview

### 1.1 Purpose

The plugin architecture enables **modular, composable context delivery** to AI assistants. Instead of monolithic prompt files, plugins provide:

1. **Structured knowledge** - Methodology, standards, best practices
2. **Reusable skills** - Testing patterns, design patterns, code generation
3. **Federated composition** - Corporate standards + division rules + team preferences + project specifics
4. **Version control** - Plugins are versioned, dependencies tracked

### 1.2 The Generic Pattern (Technology-Neutral)

**Core Concept**: AI assistants need **context** to provide valuable guidance. Context includes:
- Methodology (how to build software)
- Standards (coding style, testing requirements)
- Skills (reusable capabilities like test generation)
- Project specifics (tech stack, architecture decisions)

**The Pattern**:
```
┌──────────────────────────────────────────┐
│  Plugin = Package of Context             │
│                                          │
│  - Metadata (name, version, deps)       │
│  - Configuration (YAML/JSON)            │
│  - Documentation (markdown)              │
│  - Skills (optional - executable)       │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│  Plugin Loading = Context Composition    │
│                                          │
│  Corporate Plugin (base standards)      │
│     ↓ (inherits + overrides)            │
│  Division Plugin (specific rules)       │
│     ↓ (inherits + overrides)            │
│  Team Plugin (preferences)              │
│     ↓ (inherits + overrides)            │
│  Project Plugin (local config)          │
│                                          │
│  = Final Context (sent to AI)           │
└──────────────────────────────────────────┘
```

**Key Properties**:
1. **Composable** - Plugins stack and override
2. **Versioned** - SemVer (major.minor.patch)
3. **Declarative** - Configuration, not code
4. **Portable** - Works across different AI tools (with adapters)

---

## 2. Architecture Decision Records

### ADR-001: Plugin Format - JSON Metadata + YAML Configuration

**Context**:
- **Requirements**: REQ-F-PLUGIN-001 (marketplace support), REQ-NFR-FEDERATE-001 (composition)
- **Ecosystem Constraints**:
  - Claude Code expects JSON for plugin metadata
  - YAML is more human-readable for configuration
  - Git-friendly format needed (line-by-line diffs)

**Decision**:
- **Metadata**: JSON (`.claude-plugin/plugin.json`)
- **Configuration**: YAML (`config/*.yml`)
- **Documentation**: Markdown (`docs/*.md`, `README.md`)

**Rejected Alternatives**:
1. All JSON - Less readable for large configs
2. All YAML - Claude Code requires JSON metadata
3. TOML - Less ecosystem support

**Rationale**:
| Aspect | JSON+YAML | All JSON | All YAML | Score |
|--------|-----------|----------|----------|-------|
| Claude Code compat | ✅ Native | ✅ Native | ❌ Adapter needed | 9/10 |
| Readability | ✅ Best | ⚠️ Verbose | ✅ Good | 9/10 |
| Git-friendly | ✅ Good | ⚠️ OK | ✅ Good | 9/10 |
| Ecosystem | ✅ Both common | ✅ Universal | ⚠️ Less common | 8/10 |

**Constraints Imposed**:
- Code stage: Must parse both JSON and YAML
- Installers: Must handle both formats
- Documentation: Must explain both formats

---

### ADR-002: Plugin Categories - Methodology, Skills, Standards, Bundles

**Context**:
- **Requirements**: REQ-F-PLUGIN-003 (plugin bundles)
- **Ecosystem Constraints**:
  - Different users need different capabilities
  - Some want full methodology, others just coding standards
  - Bundles reduce installation complexity

**Decision**:
Four plugin categories:

1. **Methodology** - Complete SDLC processes (7-stage AI SDLC)
2. **Skills** - Reusable capabilities (test generation, design patterns)
3. **Standards** - Language/tech-specific rules (Python PEP 8, TypeScript ESLint)
4. **Bundles** - Pre-packaged combinations (startup, enterprise, qa)

**Rationale**:
- **Modularity**: Install only what you need
- **Composition**: Combine multiple plugins
- **Discovery**: Clear categorization in marketplace
- **Flexibility**: Bundles for common use cases, à la carte for custom needs

**Examples**:
```
Methodology:
  - aisdlc-methodology (7-stage SDLC)
  - agile-methodology (Scrum/Kanban)

Skills:
  - testing-skills (test generation, coverage)
  - code-skills (refactoring, patterns)
  - design-skills (architecture, ADRs)

Standards:
  - python-standards (PEP 8, pytest)
  - typescript-standards (ESLint, Prettier)

Bundles:
  - startup-bundle (methodology + code-skills + python-standards)
  - enterprise-bundle (all skills + compliance)
  - qa-bundle (testing-skills + system-test-skills)
```

---

### ADR-003: Dependency Management - NPM-Style SemVer

**Context**:
- **Requirements**: REQ-F-PLUGIN-004 (versioning and dependencies)
- **Ecosystem Constraints**:
  - Claude Code uses npm-style package management
  - Developers familiar with SemVer (^1.0.0)

**Decision**:
- Use SemVer (major.minor.patch)
- Declare dependencies in plugin.json
- Support version ranges (^, ~, >=)

**Example**:
```json
{
  "name": "python-standards",
  "version": "1.2.3",
  "dependencies": {
    "aisdlc-core": "^3.0.0",
    "aisdlc-methodology": ">=2.0.0 <3.0.0"
  }
}
```

**Constraints Imposed**:
- Breaking changes → major version bump
- New features → minor version bump
- Bug fixes → patch version bump
- Plugin installer must resolve dependencies

---

## 3. Plugin Structure

### 3.1 Directory Layout

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json          # Metadata (name, version, deps, keywords)
├── config/
│   ├── config.yml           # Main configuration
│   ├── stages_config.yml    # 7-stage specifications (optional)
│   └── *.yml                # Additional configs
├── docs/
│   ├── README.md            # Plugin documentation
│   ├── principles/          # Principles documentation
│   ├── processes/           # Process documentation
│   └── guides/              # User guides
├── skills/                  # Optional: executable skills
│   ├── skill-name.md        # Skill prompts
│   └── *.py                 # Skill implementations (optional)
├── project.json             # Optional: project metadata
└── README.md                # Quick start guide
```

### 3.2 Plugin Metadata Schema (.claude-plugin/plugin.json)

```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "displayName": "Human Readable Name",
  "description": "What this plugin provides",
  "author": "Author Name or Org",
  "license": "MIT",
  "keywords": ["keyword1", "keyword2"],
  "homepage": "https://github.com/org/repo",

  "configuration": {
    "main_config": "config/config.yml",
    "stages": "config/stages_config.yml",
    "reference": "../../docs/reference.md"
  },

  "documentation": {
    "overview": "docs/README.md",
    "guide": "docs/GUIDE.md"
  },

  "dependencies": {
    "plugin-name": "^1.0.0"
  },

  "skills": {
    "enabled": true,
    "paths": ["skills/"]
  },

  "capabilities": {
    "capability_name": {
      "description": "What it does",
      "skills": ["skill-1", "skill-2"]
    }
  },

  "stages": {
    "stage_name": {
      "section": "4.0",
      "agent": "Agent Name",
      "purpose": "What this stage does"
    }
  }
}
```

**Required Fields**:
- `name` - Unique identifier (lowercase, hyphens)
- `version` - SemVer string
- `displayName` - Human-readable name
- `description` - Brief description
- `author` - Author/organization

**Optional Fields**:
- `license` - License (MIT, Apache-2.0, etc.)
- `keywords` - For marketplace discovery
- `homepage` - Repository or documentation URL
- `configuration` - Paths to config files
- `documentation` - Paths to docs
- `dependencies` - Required plugins
- `skills` - Executable skills configuration
- `capabilities` - What this plugin can do
- `stages` - SDLC stage definitions

---

## 4. Federated Plugin Loading

### 4.1 Loading Order (Priority)

Plugins load in hierarchical order, with later plugins overriding earlier ones:

```
1. Corporate Marketplace
   └─ aisdlc-methodology@2.0.0
   └─ corporate-security-standards@1.0.0

2. Division Marketplace
   └─ backend-division-standards@1.2.0

3. Team Marketplace
   └─ payment-team-standards@1.0.0

4. Project Plugin (.claude-claude-code/plugins/my-project/)
   └─ project-specific-config

= Final Context (sent to Claude Code)
```

**Override Rules**:
- Later plugins override earlier ones
- Configuration merges (deep merge for objects, replace for primitives)
- Documentation appends (not replace)
- Skills combine (all available)

### 4.2 Configuration Merging

**Example**:

Corporate plugin:
```yaml
code:
  testing:
    coverage_minimum: 80
    frameworks: [pytest]
```

Project plugin:
```yaml
code:
  testing:
    coverage_minimum: 95  # Override corporate
    frameworks: [pytest, hypothesis]  # Extend corporate
```

Final merged configuration:
```yaml
code:
  testing:
    coverage_minimum: 95  # From project
    frameworks: [pytest, hypothesis]  # Merged array
```

**Merge Strategy**:
- Primitives (strings, numbers, booleans): Replace
- Arrays: Concatenate (deduplicate)
- Objects: Deep merge (recursive)

---

## 5. Implemented Plugins

### 5.1 Plugin Inventory

**Total Plugins**: 13 (10 individual + 3 bundles)

#### Core Plugins

**1. aisdlc-core** (v3.0.0)
- **Category**: Methodology (foundation)
- **Purpose**: Core AI SDLC framework
- **Dependencies**: None
- **Size**: ~500 lines

**2. aisdlc-methodology** (v2.0.0) ⭐
- **Category**: Methodology
- **Purpose**: Complete 7-stage AI SDLC
- **Dependencies**: None (foundation)
- **Configuration**: stages_config.yml (1,273 lines), config.yml (Key Principles)
- **Stages**: Requirements, Design, Tasks, Code, System Test, UAT, Runtime Feedback
- **Size**: ~15KB total

#### Skills Plugins

**3. testing-skills** (v1.0.0)
- **Category**: Skills
- **Purpose**: Test coverage validation, test generation, integration testing
- **Dependencies**: aisdlc-core@^3.0.0
- **Capabilities**: coverage_validation (sensor), test_generation (actuator), integration_testing, coverage_reporting
- **Size**: ~800 lines

**4. code-skills** (v1.0.0)
- **Category**: Skills
- **Purpose**: Code refactoring, design patterns, code quality
- **Dependencies**: aisdlc-core@^3.0.0
- **Capabilities**: refactoring, pattern_application, code_review
- **Size**: ~600 lines

**5. design-skills** (v1.0.0)
- **Category**: Skills
- **Purpose**: Architecture, ADRs, component design
- **Dependencies**: aisdlc-core@^3.0.0
- **Capabilities**: architecture_design, adr_creation, component_modeling
- **Size**: ~700 lines

**6. requirements-skills** (v1.0.0)
- **Category**: Skills
- **Purpose**: Requirements elicitation, validation, traceability
- **Dependencies**: aisdlc-core@^3.0.0
- **Capabilities**: requirements_extraction, validation, traceability_mapping
- **Size**: ~500 lines

**7. runtime-skills** (v1.0.0)
- **Category**: Skills
- **Purpose**: Deployment, monitoring, telemetry, feedback loops
- **Dependencies**: aisdlc-core@^3.0.0
- **Capabilities**: deployment_automation, telemetry_setup, feedback_analysis
- **Size**: ~600 lines

#### Standards Plugins

**8. python-standards** (v1.0.0)
- **Category**: Standards
- **Purpose**: Python PEP 8, pytest, type hints, tooling
- **Dependencies**: aisdlc-methodology@^2.0.0
- **Configuration**: PEP 8 rules, pytest configuration, mypy settings
- **Size**: ~400 lines

**9. principles-key** (v1.0.0)
- **Category**: Methodology
- **Purpose**: Key Principles principles (TDD, Fail Fast, etc.)
- **Dependencies**: None
- **Documentation**: KEY_PRINCIPLES.md, TDD_WORKFLOW.md
- **Size**: ~300 lines

#### Plugin Bundles

**10. startup-bundle** (v1.0.0)
- **Category**: Bundle
- **Purpose**: Essential plugins for new projects
- **Includes**: aisdlc-methodology, code-skills, testing-skills, python-standards
- **Dependencies**: Bundles don't have code, just declare dependencies

**11. datascience-bundle** (v1.0.0)
- **Category**: Bundle
- **Purpose**: Data science and ML projects
- **Includes**: aisdlc-methodology, requirements-skills, testing-skills, runtime-skills

**12. qa-bundle** (v1.0.0)
- **Category**: Bundle
- **Purpose**: Quality assurance focus
- **Includes**: testing-skills, design-skills, runtime-skills

**13. enterprise-bundle** (v1.0.0)
- **Category**: Bundle
- **Purpose**: Complete enterprise suite
- **Includes**: All plugins (methodology + all skills + standards)

### 5.2 Plugin Dependency Graph

```
aisdlc-core (v3.0.0)
  ↑
  ├─ testing-skills
  ├─ code-skills
  ├─ design-skills
  ├─ requirements-skills
  └─ runtime-skills

aisdlc-methodology (v2.0.0)
  ↑
  └─ python-standards

principles-key (standalone)

Bundles:
  startup-bundle → [methodology, code-skills, testing-skills, python-standards]
  datascience-bundle → [methodology, requirements-skills, testing-skills, runtime-skills]
  qa-bundle → [testing-skills, design-skills, runtime-skills]
  enterprise-bundle → [ALL]
```

---

## 6. Claude Code Implementation

### 6.1 Claude Code Integration

**How Claude Code Uses Plugins**:

1. **Plugin Discovery**:
   - Claude Code scans `.claude-plugin/plugin.json` files
   - Indexes plugins by name and version
   - Resolves dependencies

2. **Plugin Loading**:
   - Loads configuration files (YAML parsed into context)
   - Loads documentation (markdown included in prompt)
   - Enables skills (if `skills.enabled: true`)

3. **Context Injection**:
   - Plugin content → Claude's system prompt
   - Available when user asks questions
   - Can reference plugin documentation, configuration, skills

**Marketplace Integration**:

`.claude/settings.json`:
```json
{
  "extraKnownMarketplaces": {
    "aisdlc": {
      "source": {
        "source": "github",
        "repo": "foolishimp/ai_sdlc_method"
      }
    }
  }
}
```

**Installation Commands**:
```bash
# Add marketplace
/plugin marketplace add foolishimp/ai_sdlc_method

# Install plugin
/plugin install @aisdlc/aisdlc-methodology

# List installed
/plugin list

# Update plugin
/plugin update @aisdlc/aisdlc-methodology
```

### 6.2 Plugin Loading in Claude Code

**File Locations**:
- **Global Plugins**: `~/.claude/claude-code/plugins/`
- **Project Plugins**: `./.claude-claude-code/plugins/`

**Loading Order**:
1. Global plugins (shared across all projects)
2. Project plugins (specific to current project)
3. Merge configurations (project overrides global)

**Configuration Loading**:
```
plugin.json → metadata
  ↓
config/*.yml → parsed into structured data
  ↓
docs/*.md → loaded as reference documentation
  ↓
All combined → sent to Claude Code as system context
```

---

## 7. Generic Pattern Adapters

### 7.1 Portability to Other AI Tools

The plugin pattern is **Claude Code specific**, but the **concept is portable**:

**For GitHub Copilot**:
- Store plugins in `.github/copilot/`
- Use `.copilot-plugin.json` metadata
- Same YAML configuration structure
- Copilot loads as workspace context

**For Cursor**:
- Store plugins in `.cursor/claude-code/plugins/`
- Use `.cursor-plugin.json` metadata
- Same configuration structure
- Cursor loads as project context

**For Generic LLMs** (via MCP):
- MCP server loads plugins from storage
- Exposes plugin content as MCP resources
- LLM queries MCP for context
- See: [MCP Service](../../mcp_service/README.md)

### 7.2 Plugin Adapter Pattern

```
┌─────────────────────────────────────┐
│  Generic Plugin Format              │
│                                     │
│  - plugin-metadata.json             │
│  - config/*.yml                     │
│  - docs/*.md                        │
└─────────────────────────────────────┘
          ↓
┌─────────────────────────────────────┐
│  Tool-Specific Adapter              │
│                                     │
│  - Claude Code: .claude-plugin/     │
│  - Copilot: .copilot-plugin/        │
│  - Cursor: .cursor-plugin/          │
│  - MCP: mcp-plugin-loader           │
└─────────────────────────────────────┘
          ↓
┌─────────────────────────────────────┐
│  LLM Context (system prompt)        │
└─────────────────────────────────────┘
```

---

## 8. Plugin Installers

### 8.1 Installation Scripts

**Location**: `installers/setup_plugins.py`

**Functionality**:
1. Reads marketplace configuration
2. Fetches plugin from GitHub or local path
3. Copies plugin to `.claude-claude-code/plugins/`
4. Resolves dependencies
5. Validates plugin.json schema
6. Updates project settings

**Usage**:
```bash
# Install single plugin
python installers/setup_plugins.py --plugin aisdlc-methodology

# Install bundle
python installers/setup_plugins.py --bundle startup

# Install from local path
python installers/setup_plugins.py --local ../my-plugin

# Non-interactive mode (CI/CD)
python installers/setup_plugins.py --plugin aisdlc-methodology --non-interactive
```

### 8.2 Marketplace Registry

**Location**: `marketplace.json`

```json
{
  "name": "AI SDLC Method Marketplace",
  "version": "1.0.0",
  "plugins": {
    "aisdlc-methodology": {
      "path": "claude-code/plugins/aisdlc-methodology",
      "version": "2.0.0",
      "category": "methodology"
    },
    "testing-skills": {
      "path": "claude-code/plugins/testing-skills",
      "version": "1.0.0",
      "category": "skills"
    }
  },
  "bundles": {
    "startup": {
      "plugins": [
        "aisdlc-methodology@^2.0.0",
        "code-skills@^1.0.0",
        "testing-skills@^1.0.0"
      ]
    }
  }
}
```

---

## 9. Quality Gates

### 9.1 Plugin Validation

**Every plugin must**:
- ✅ Have valid plugin.json (passes JSON schema)
- ✅ Declare all dependencies
- ✅ Have README.md with installation instructions
- ✅ Use SemVer versioning
- ✅ Include license information

**Configuration validation**:
- ✅ YAML files parse without errors
- ✅ Required sections present
- ✅ No circular dependencies

### 9.2 Traceability

**Plugin → Requirements**:
- Each plugin documents which requirements it implements
- Plugin metadata includes `requirements` field
- Traceability matrix maps REQ-* → Plugin

**Example**:
```json
{
  "name": "testing-skills",
  "requirements": [
    "REQ-F-TESTING-001",
    "REQ-F-TESTING-002",
    "REQ-NFR-COVERAGE-001"
  ]
}
```

---

## 10. Future Enhancements

### 10.1 Planned Features

**Short-term** (v1.1):
- [ ] Plugin hot-reloading (no restart needed)
- [ ] Plugin marketplace GUI
- [ ] Automated dependency resolution

**Mid-term** (v1.2):
- [ ] Plugin testing framework
- [ ] Plugin CI/CD pipeline
- [ ] Plugin analytics (usage tracking)

**Long-term** (v2.0):
- [ ] Cross-tool plugin format (unified adapter)
- [ ] Plugin composition language (DSL)
- [ ] Plugin marketplace with ratings/reviews

### 10.2 Open Questions

1. **Plugin versioning conflicts**: What if two plugins require incompatible versions of a dependency?
   - Current: Manual resolution
   - Proposed: Semantic version resolution (npm-style)

2. **Plugin size limits**: Should we limit plugin size?
   - Current: No limit
   - Proposed: Warn if >10MB, fail if >50MB

3. **Plugin security**: How to prevent malicious plugins?
   - Current: Manual review
   - Proposed: Signing + sandboxing

---

## 11. Implementation Status

### 11.1 Current Status

✅ **Implemented**:
- Plugin metadata schema (plugin.json)
- 13 plugins created (10 individual + 3 bundles)
- Plugin installer (setup_plugins.py)
- Marketplace registry (marketplace.json)
- Federated loading (project overrides global)
- Dependency declarations

⚠️ **Partial**:
- Dependency resolution (declared, not enforced)
- Plugin validation (manual, not automated)
- Marketplace GUI (CLI only)

❌ **Not Implemented**:
- Hot-reloading
- Plugin testing framework
- Cross-tool adapters (Copilot, Cursor)
- Plugin analytics

### 11.2 Code Artifacts

**Implemented**:
- `claude-code/plugins/` - 13 plugins
- `installers/setup_plugins.py` - Plugin installer
- `marketplace.json` - Marketplace registry
- `PLUGIN_GUIDE.md` - User guide

**Tests**:
- No automated tests yet (manual validation only)

**Traceability**:
- REQ-F-PLUGIN-001 → claude-code/plugins/, marketplace.json ✅
- REQ-F-PLUGIN-002 → Federated loading (project overrides) ✅
- REQ-F-PLUGIN-003 → Plugin bundles (startup, qa, enterprise) ✅
- REQ-F-PLUGIN-004 → SemVer in plugin.json, dependencies declared ⚠️ (not enforced)

---

## 12. References

**Requirements**:
- [AI_SDLC_REQUIREMENTS.md](../requirements/AI_SDLC_REQUIREMENTS.md)

**Related Design**:
- [AI_SDLC_UX_DESIGN.md](AI_SDLC_UX_DESIGN.md)
- [COMMAND_SYSTEM.md](COMMAND_SYSTEM.md) (to be created)
- [TEMPLATE_SYSTEM.md](TEMPLATE_SYSTEM.md) (to be created)

**Implementation**:
- [claude-code/plugins/README.md](../../claude-code/plugins/README.md)
- [PLUGIN_GUIDE.md](../../PLUGIN_GUIDE.md)
- [installers/setup_plugins.py](../../installers/setup_plugins.py)

---

**Document Status**: Draft
**Next Review**: After Task #2, #3 completion (Template & Command design docs)
