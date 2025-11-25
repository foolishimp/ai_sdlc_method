# Roo Code AISDLC Design

## Overview

This document describes the high-level architecture for implementing AISDLC on Roo Code.

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Roo Code Extension                        │
├─────────────────────────────────────────────────────────────┤
│  Custom Modes (.roo/modes/)                                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │ requirements│ │   design    │ │    tasks    │            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │    code     │ │ system-test │ │     uat     │            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
│  ┌─────────────┐                                             │
│  │   runtime   │                                             │
│  └─────────────┘                                             │
├─────────────────────────────────────────────────────────────┤
│  Custom Instructions (.roo/rules/)                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │key-principles│ │tdd-workflow │ │ req-tagging │            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
├─────────────────────────────────────────────────────────────┤
│  Memory Bank (.roo/memory-bank/)                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │projectbrief │ │  techstack  │ │activecontext│            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
├─────────────────────────────────────────────────────────────┤
│  Shared Workspace (.ai-workspace/)                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │   tasks/    │ │ templates/  │ │   config/   │            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

## Mode Definition Schema

```json
{
  "slug": "aisdlc-<stage>",
  "name": "AISDLC <Stage> Agent",
  "roleDefinition": "<Stage persona description>",
  "groups": ["read", "edit", "command", "mcp", "browser"],
  "customInstructions": "<Stage-specific instructions>",
  "source": "project"
}
```

## Tool Groups

| Group | Description | Stages |
|-------|-------------|--------|
| `read` | File reading | All |
| `edit` | File modification | Design, Tasks, Code |
| `command` | Terminal commands | Code, System Test |
| `mcp` | MCP server access | All |
| `browser` | Web browsing | Requirements, UAT |

## Integration Points

1. **Workspace** - Shared `.ai-workspace/` structure
2. **Traceability** - REQ-* tagging in all outputs
3. **Memory Bank** - Persistent context across sessions
4. **Rules** - Shared instructions across modes
