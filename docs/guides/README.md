# AI SDLC Methodology - User Guides

**Purpose**: Practical guides for using the AI SDLC methodology in your projects

---

## Available Guides

### Core Guides

1. **[Plugin Guide](PLUGIN_GUIDE.md)** - Complete guide to installing and using AI SDLC plugins
   - Installation and setup
   - Plugin architecture
   - Creating project-specific plugins
   - Federated plugin systems
   - Troubleshooting

2. **[New Project Setup](NEW_PROJECT_SETUP.md)** - Step-by-step project setup guide
   - Installing the aisdlc-methodology plugin
   - Project structure and workspace setup
   - Running through the 7 stages
   - Available slash commands
   - Common workflows
   - Updating existing projects

3. **[Complete Journey](JOURNEY.md)** - Full walkthrough from intent to UAT
   - Complete happy path through all 7 stages
   - Real examples with concrete code
   - Requirement traceability in action
   - Time to complete: 2-3 hours

---

## Quick Reference

### What is the AI SDLC Methodology?

A complete **7-stage lifecycle framework** for intent-driven software development:

1. **Requirements** - Transform intent into REQ-* keys
2. **Design** - Create technical solutions
3. **Tasks** - Break work into trackable units
4. **Code** - Implement with TDD (RED → GREEN → REFACTOR)
5. **System Test** - Validate with BDD (Given/When/Then)
6. **UAT** - Business validation and sign-off
7. **Runtime Feedback** - Production telemetry and feedback loops

### Key Features

- **Requirement Traceability** - Track REQ-F-*, REQ-NFR-*, REQ-DATA-* from intent to runtime
- **AI Agent Specifications** - 7 stage-specific agents with detailed configurations (790 lines)
- **42 Skills** - Reusable capabilities across all stages
- **8 Commands** - Slash commands for workflow management
- **4 Hooks** - Automated methodology integration
- **Plugin Architecture** - Installable, versioned, federated standards

---

## Quick Start

### 1. Install the Plugin

The AI SDLC methodology is available as a Claude Code plugin:

```bash
# Add to your Claude Code plugin settings
# Location: claude-code/.claude-plugin/plugins/aisdlc-methodology
```

The plugin includes:
- 7 stage agents
- 42 skills across 7 categories
- 8 slash commands (/aisdlc-*)
- Complete stage configurations

### 2. Start Using It

Ask Claude to help with any SDLC stage:

```
"Generate requirements from INTENT.md using the Requirements Agent"
"Design the authentication service following the Design Agent specs"
"Write tests following TDD workflow from the Code Agent"
```

Claude has full access to the 7-stage methodology, including:
- Stage-specific workflows
- Quality gates and validation
- Requirement key formats
- Traceability patterns

---

## Prerequisites

Before using these guides:

**Required**:
- Claude Code installed (CLI or VS Code extension)
- Git installed
- Basic understanding of software development

**Recommended Reading**:
1. [AI SDLC Overview](../requirements/AI_SDLC_OVERVIEW.md) - High-level introduction
2. [AI SDLC Requirements](../requirements/AI_SDLC_REQUIREMENTS.md) - Complete methodology specification
3. [AI SDLC Concepts](../requirements/AI_SDLC_CONCEPTS.md) - Key concepts and theory

---

## Role-Based Focus Areas

While the guides are general-purpose, here's what each role should focus on:

### For Developers
- **[New Project Setup](NEW_PROJECT_SETUP.md)** - Focus on Code stage (Stage 4)
- **Code Agent** - TDD workflow, Key Principles
- **Commands**: `/aisdlc-status`, `/aisdlc-checkpoint-tasks`, `/aisdlc-commit-task`

### For Architects & Tech Leads
- **[Journey Guide](JOURNEY.md)** - Focus on Requirements and Design stages (Stages 1-2)
- **Requirements Agent**, **Design Agent**
- Review ADRs in `/docs/design/claude_aisdlc/adrs/`

### For QA Engineers
- **[Journey Guide](JOURNEY.md)** - Focus on System Test and UAT stages (Stages 5-6)
- **System Test Agent**, **UAT Agent**
- BDD testing patterns

### For Product Owners & Managers
- **[Plugin Guide](PLUGIN_GUIDE.md)** - Understanding the complete framework
- **Requirements Agent**, **Tasks Agent**, **Runtime Feedback Agent**
- Requirement traceability and governance

---

## Project Structure

After installing the methodology plugin, your project will have access to:

```
.claude-plugin/plugins/aisdlc-methodology/
├── agents/                    # 7 stage-specific personas
│   ├── aisdlc-requirements-agent.md
│   ├── aisdlc-design-agent.md
│   ├── aisdlc-tasks-agent.md
│   ├── aisdlc-code-agent.md
│   ├── aisdlc-system-test-agent.md
│   ├── aisdlc-uat-agent.md
│   └── aisdlc-runtime-feedback-agent.md
├── commands/                  # 8 slash commands
│   ├── aisdlc-checkpoint-tasks.md
│   ├── aisdlc-commit-task.md
│   ├── aisdlc-finish-task.md
│   ├── aisdlc-help.md
│   ├── aisdlc-refresh-context.md
│   ├── aisdlc-release.md
│   ├── aisdlc-status.md
│   └── aisdlc-update.md
├── skills/                    # 42 skills in 7 categories
│   ├── code/
│   ├── core/
│   ├── design/
│   ├── principles/
│   ├── requirements/
│   ├── runtime/
│   └── testing/
├── config/
│   ├── stages_config.yml     # 790-line stage specifications
│   └── config.yml            # Key Principles configuration
└── templates/                # Workspace scaffolding
    └── .ai-workspace/
```

---

## Additional Resources

### Documentation
- [Complete Requirements](../requirements/AI_SDLC_REQUIREMENTS.md) - Full methodology specification
- [Appendices](../requirements/AI_SDLC_APPENDICES.md) - Category theory, mathematics
- [Traceability Matrix](../TRACEABILITY_MATRIX.md) - Complete requirement tracking

### Design Documentation
- [Claude Code Implementation](../design/claude_aisdlc/) - Claude-specific design
- [ADRs](../design/claude_aisdlc/adrs/) - Architecture decision records
- [Plugin Architecture](../design/claude_aisdlc/PLUGIN_ARCHITECTURE.md)

### Information
- [Skills Inventory](../info/SKILLS_INVENTORY.md) - All 42 skills documented
- [Agents vs Skills](../info/AGENTS_VS_SKILLS.md) - Understanding the distinction
- [Component Inventory](../info/INVENTORY.md) - Complete component catalog

---

## Getting Help

- **Issues**: https://github.com/foolishimp/ai_sdlc_method/issues
- **Discussions**: https://github.com/foolishimp/ai_sdlc_method/discussions
- **Examples**: See `examples/` directory in this repository

---

## Contributing

These guides are living documents. Contributions welcome:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

Focus areas for contribution:
- Real-world examples
- Role-specific best practices
- Common pitfalls and solutions
- Integration patterns

---

**"Excellence or nothing"** 🔥
