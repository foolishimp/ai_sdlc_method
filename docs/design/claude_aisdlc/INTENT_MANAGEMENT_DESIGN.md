# Intent Management - Design Document

**Document Type**: Technical Design Specification
**Project**: ai_sdlc_method (claude_aisdlc solution)
**Version**: 1.0
**Date**: 2025-12-03
**Status**: Draft
**Stage**: Design (Section 5.0)

---

## Requirements Traceability

This design implements the following requirements:

| Requirement | Description | Priority |
|-------------|-------------|----------|
| REQ-INTENT-001 | Intent Capture | Critical |
| REQ-INTENT-002 | Intent Classification | High |
| REQ-INTENT-003 | Eco-Intent Generation | Medium |

**Source**: [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) Section 1

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Data Structures](#2-data-structures)
3. [Storage Architecture](#3-storage-architecture)
4. [Workflows](#4-workflows)
5. [Integration Points](#5-integration-points)
6. [Validation](#6-validation)
7. [Examples](#7-examples)
8. [Implementation Guidance](#8-implementation-guidance)

---

## 1. Executive Summary

### 1.1 Purpose

Intent Management is the **entry point** to the AI SDLC. It provides structured capture, classification, and persistence of intents (desires for change) that flow through all seven SDLC stages.

### 1.2 Design Principles

1. **File-based** - No external dependencies, version-controlled
2. **Human-readable** - YAML format for easy editing
3. **Traceable** - Unique INT-* keys link to downstream artifacts
4. **Extensible** - Schema supports custom metadata
5. **Atomic** - Each intent is a single file

### 1.3 Key Design Decisions

| Decision | Rationale | Requirement |
|----------|-----------|-------------|
| One intent per file | Atomic commits, easier conflict resolution | REQ-INTENT-001 |
| YAML format | Human-readable, git-friendly | REQ-INTENT-001 |
| INT-* key generation | Timestamp + counter = unique + sortable | REQ-INTENT-001 |
| Work type taxonomy | Maps to control regimes (Methodology 2.4.2) | REQ-INTENT-002 |
| Separate eco-intents | Different generation workflow | REQ-INTENT-003 |

---

## 2. Data Structures

### 2.1 Intent Schema

**File**: Intent metadata in YAML format

```yaml
# Intent identifier (generated)
id: INT-20251203-001

# Classification
classification:
  work_type: create | update | remediate | read | delete
  category: feature | bug | refactor | documentation | infrastructure
  priority: critical | high | medium | low
  impact: high | medium | low
  effort_estimate: "2-5 days"  # Optional, human estimate

# Core fields
title: "Add user authentication to portal"
description: |
  Users need to log in with email/password to access the customer portal.
  Authentication should integrate with existing SSO provider.

  Acceptance criteria:
  - Login page with email/password fields
  - Integration with Auth0 SSO
  - Session management with 30-minute timeout
  - "Remember me" checkbox for 7-day sessions

# Origin information
source:
  type: human | runtime_feedback | ecosystem_monitor | manual
  author: "john.doe@company.com"
  timestamp: "2025-12-03T14:32:15Z"
  context: |
    Customer support reports indicate 40% of users abandon
    the portal due to lack of self-service authentication.

# Status tracking
status: draft | approved | in_progress | completed | rejected | blocked
status_history:
  - status: draft
    timestamp: "2025-12-03T14:32:15Z"
    author: "john.doe@company.com"
  - status: approved
    timestamp: "2025-12-03T15:10:22Z"
    author: "jane.smith@company.com"
    comment: "Approved by product owner"

# Relationships
related_intents:
  - INT-20251120-015  # "Implement SSO integration"
  - INT-20251201-008  # "Add session management"

derived_requirements: []  # Populated by Requirements stage
  # - REQ-F-AUTH-001
  # - REQ-NFR-SEC-001

# Lifecycle tracking
lifecycle:
  requirements_stage:
    started: "2025-12-03T16:00:00Z"
    completed: null
    agent: "AISDLC Requirements Agent"
  design_stage:
    started: null
    completed: null
    agent: null
  # ... (other stages)

# Custom metadata (extensible)
metadata:
  business_value: "Increase portal adoption by 25%"
  customer_segment: "enterprise"
  compliance: ["SOC2", "GDPR"]
  tags: ["security", "authentication", "portal"]

# Version tracking
version: 1
created_at: "2025-12-03T14:32:15Z"
updated_at: "2025-12-03T15:10:22Z"
```

### 2.2 Intent Key Generation Algorithm

**Purpose**: Generate unique, sortable, human-readable intent identifiers

**Format**: `INT-YYYYMMDD-NNN`

**Components**:
- `INT-` - Prefix indicating intent
- `YYYYMMDD` - Creation date (enables chronological sorting)
- `NNN` - Zero-padded counter (001-999) for same-day intents

**Algorithm**:

```python
def generate_intent_id(existing_ids: list[str]) -> str:
    """
    Generate unique intent ID.

    Args:
        existing_ids: List of existing intent IDs for today

    Returns:
        Unique intent ID in format INT-YYYYMMDD-NNN

    Examples:
        >>> generate_intent_id([])
        'INT-20251203-001'
        >>> generate_intent_id(['INT-20251203-001', 'INT-20251203-002'])
        'INT-20251203-003'
    """
    from datetime import datetime

    # Get current date
    today = datetime.now().strftime("%Y%m%d")

    # Filter IDs from today
    today_prefix = f"INT-{today}-"
    today_ids = [
        int(id.split("-")[-1])
        for id in existing_ids
        if id.startswith(today_prefix)
    ]

    # Find next counter
    if not today_ids:
        counter = 1
    else:
        counter = max(today_ids) + 1

    # Generate ID
    return f"INT-{today}-{counter:03d}"
```

**Collision Handling**:
- Atomic file creation with `O_EXCL` flag (fail if exists)
- Retry with next counter on collision
- Max 999 intents per day per workspace

### 2.3 Work Type Taxonomy

**Purpose**: Map intents to control regimes (Methodology Section 2.4.2)

| Work Type | Definition | Control Regime | Example |
|-----------|------------|----------------|---------|
| `create` | New capability or feature | Standard | "Add payment processing" |
| `update` | Change existing behavior | Standard | "Improve search algorithm" |
| `remediate` | Fix production incident | High scrutiny | "Fix authentication timeout" |
| `read` | Analyze or investigate | Lightweight | "Analyze query performance" |
| `delete` | Retire capability | High scrutiny | "Remove deprecated API" |

**Classification Rules**:

```yaml
# REQ-INTENT-002: Intent Classification

work_type_rules:
  create:
    indicators: ["add", "new", "implement", "build"]
    control_regime: standard
    quality_gates: ["design_review", "code_review", "integration_test"]

  update:
    indicators: ["change", "modify", "improve", "enhance", "refactor"]
    control_regime: standard
    quality_gates: ["design_review", "code_review", "regression_test"]

  remediate:
    indicators: ["fix", "bug", "incident", "outage", "error", "failure"]
    control_regime: high_scrutiny
    quality_gates: ["root_cause_analysis", "design_review", "code_review", "regression_test", "production_validation"]
    required_fields: ["incident_id", "root_cause"]

  read:
    indicators: ["analyze", "investigate", "research", "explore"]
    control_regime: lightweight
    quality_gates: ["findings_review"]

  delete:
    indicators: ["remove", "retire", "deprecate", "delete"]
    control_regime: high_scrutiny
    quality_gates: ["impact_analysis", "migration_plan", "rollback_plan"]
    required_fields: ["deprecation_timeline", "migration_guide"]
```

### 2.4 Eco-Intent Schema

**Purpose**: Capture intents generated by ecosystem monitoring (REQ-INTENT-003)

**Format**: Extends base intent schema with ecosystem context

```yaml
# Eco-intent identifier
id: INT-ECO-20251203-001

# Classification (automatically assigned)
classification:
  work_type: update | remediate  # Based on eco-event type
  category: infrastructure | security | dependency
  priority: critical | high | medium | low  # Based on impact
  impact: high | medium | low  # Assessed from eco-event

# Eco-specific fields
eco_event:
  type: security_vulnerability | deprecation | api_change | compliance_update
  detected_at: "2025-12-03T08:00:00Z"
  source: "GitHub Security Advisory" | "npm audit" | "API changelog" | "compliance scanner"

  # Security vulnerability
  vulnerability:
    cve_id: "CVE-2025-12345"
    severity: critical | high | medium | low
    affected_package: "express@4.17.1"
    fixed_version: "4.18.2"
    cwe_ids: ["CWE-79"]

  # Deprecation
  deprecation:
    deprecated_feature: "Node.js 16"
    deprecation_date: "2025-06-01"
    end_of_life_date: "2025-12-31"
    replacement: "Node.js 20"
    migration_guide_url: "https://..."

  # API change
  api_change:
    api_name: "Stripe Checkout API"
    change_type: breaking | non_breaking
    effective_date: "2026-01-01"
    changelog_url: "https://..."

  # Compliance update
  compliance_update:
    regulation: "GDPR" | "SOC2" | "HIPAA"
    change_description: "New data retention requirements"
    effective_date: "2026-03-01"
    compliance_guide_url: "https://..."

# Impact assessment (auto-generated)
impact_assessment:
  affected_files: []  # List of files using deprecated feature
  affected_dependencies: []  # Package dependency tree
  estimated_effort: "1-3 days"
  risk_level: high | medium | low

# Standard intent fields
title: "[AUTO] Security vulnerability in express@4.17.1 (CVE-2025-12345)"
description: |
  AUTOMATICALLY GENERATED ECO-INTENT

  A critical security vulnerability (CVE-2025-12345) has been detected
  in express@4.17.1. This package is used in 12 files across the project.

  Severity: CRITICAL
  CVSS Score: 9.8
  CWE: CWE-79 (Cross-Site Scripting)

  Recommended Action:
  - Upgrade express from 4.17.1 to 4.18.2
  - Review affected endpoints for XSS vulnerabilities
  - Run security regression tests

  Affected Files:
  - src/server.js
  - src/api/routes.js
  ...

source:
  type: ecosystem_monitor
  author: "system"
  timestamp: "2025-12-03T08:00:00Z"
  context: "Detected by GitHub Security Advisory scanner"

status: draft  # Awaits human review before approval

# Rest of standard intent fields...
```

### 2.5 Intent Index Schema

**Purpose**: Fast lookup and querying of intents without parsing all files

**File**: `.ai-workspace/intents/intent_index.yml`

```yaml
# Intent index (auto-generated, do not edit manually)
index_version: 1
last_updated: "2025-12-03T16:45:00Z"

intents:
  INT-20251203-001:
    title: "Add user authentication to portal"
    work_type: create
    priority: high
    status: approved
    created_at: "2025-12-03T14:32:15Z"
    file_path: "intents/human/INT-20251203-001.yml"

  INT-ECO-20251203-001:
    title: "[AUTO] Security vulnerability in express@4.17.1"
    work_type: remediate
    priority: critical
    status: draft
    created_at: "2025-12-03T08:00:00Z"
    file_path: "intents/eco/INT-ECO-20251203-001.yml"

# Statistics
statistics:
  total_intents: 42
  by_status:
    draft: 5
    approved: 12
    in_progress: 18
    completed: 6
    rejected: 1
  by_work_type:
    create: 15
    update: 12
    remediate: 8
    read: 5
    delete: 2
  by_priority:
    critical: 3
    high: 15
    medium: 18
    low: 6
```

---

## 3. Storage Architecture

### 3.1 Directory Structure

**Location**: `.ai-workspace/intents/`

```
.ai-workspace/
└── intents/
    ├── intent_index.yml           # Fast lookup index
    ├── intent_schema.json         # JSON Schema validation
    ├── human/                     # Human-created intents
    │   ├── INT-20251203-001.yml
    │   ├── INT-20251203-002.yml
    │   └── INT-20251203-003.yml
    ├── eco/                       # Ecosystem-generated intents
    │   ├── INT-ECO-20251203-001.yml
    │   ├── INT-ECO-20251203-002.yml
    │   └── INT-ECO-20251203-003.yml
    ├── archive/                   # Completed/rejected intents (older than 90 days)
    │   ├── 2025-Q4/
    │   │   ├── INT-20251001-015.yml
    │   │   └── INT-20251015-042.yml
    │   └── 2025-Q3/
    └── templates/
        ├── intent_template.yml     # Base intent template
        └── eco_intent_template.yml # Eco-intent template
```

### 3.2 File Naming Convention

**Format**: `{work_type}/{id}.yml`

**Rules**:
- Human intents: `human/INT-YYYYMMDD-NNN.yml`
- Eco intents: `eco/INT-ECO-YYYYMMDD-NNN.yml`
- Archived intents: `archive/YYYY-QN/INT-*.yml`

**Examples**:
```
.ai-workspace/intents/human/INT-20251203-001.yml
.ai-workspace/intents/eco/INT-ECO-20251203-001.yml
.ai-workspace/intents/archive/2025-Q4/INT-20251001-015.yml
```

### 3.3 Version Control Strategy

**Git Integration**:

```gitignore
# .gitignore for intents

# DO commit
.ai-workspace/intents/**/*.yml
.ai-workspace/intents/intent_index.yml

# DO NOT commit
.ai-workspace/intents/**/*.tmp
.ai-workspace/intents/**/*.lock
```

**Branching Strategy**:
- Intents created on feature branches
- Intent IDs generated at creation time (not merge time)
- Merge conflicts resolved by keeping both intents (unique IDs)

**Commit Message Template**:
```
intent: {action} {id} - {title}

{work_type}: {category}
Priority: {priority}
Status: {status}

{description summary}
```

**Example**:
```
intent: create INT-20251203-001 - Add user authentication to portal

Work Type: create
Priority: high
Status: approved

Users need to log in with email/password to access the customer
portal. Authentication should integrate with existing SSO provider.
```

### 3.4 Archival Strategy

**Policy**: Archive intents older than 90 days with status `completed` or `rejected`

**Process**:
1. Daily cron job checks intent ages
2. Move qualifying intents to `archive/YYYY-QN/`
3. Update intent_index.yml
4. Preserve full metadata (no data loss)
5. Archive is searchable but not indexed

**Retrieval**: Manual search in archive if needed for historical analysis

---

## 4. Workflows

### 4.1 Human Intent Capture Workflow

**Purpose**: Implements REQ-INTENT-001 for human-generated intents

**Trigger**: User runs `/aisdlc-create-intent` command

**Steps**:

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User Initiates Intent                                        │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Claude Guides Interactive Capture                            │
│    - What is the desired change?                                │
│    - What is the business value?                                │
│    - What are acceptance criteria?                              │
│    - What is the priority?                                      │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Generate Intent ID                                           │
│    - Read existing IDs from .ai-workspace/intents/human/        │
│    - Generate INT-YYYYMMDD-NNN                                  │
│    - Ensure uniqueness (atomic create)                          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Classify Intent (REQ-INTENT-002)                            │
│    - Analyze description for work type indicators              │
│    - Suggest classification                                    │
│    - User confirms or overrides                                │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Create Intent File                                           │
│    - Populate intent_template.yml                              │
│    - Write to .ai-workspace/intents/human/INT-*.yml            │
│    - Set status: draft                                         │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. Update Intent Index                                          │
│    - Add entry to intent_index.yml                             │
│    - Update statistics                                         │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. Git Commit (Optional)                                        │
│    - Stage intent file                                         │
│    - Commit with template message                              │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. Display Summary                                              │
│    - Show intent ID                                            │
│    - Show file path                                            │
│    - Suggest next steps (approve, refine, or start Reqmts)    │
└─────────────────────────────────────────────────────────────────┘
```

**Command Specification**:

```bash
# Slash command definition
# File: .claude/commands/aisdlc-create-intent.md

/aisdlc-create-intent

# Description: Create a new intent for the AI SDLC
# Usage: /aisdlc-create-intent
# Agent: Requirements Agent (guides process)
```

**Interactive Prompts**:

```yaml
# Prompt sequence for intent capture

prompts:
  - step: 1
    question: "What change do you want to make?"
    hint: "Describe the desired outcome, not the implementation"
    example: "Users should be able to log in with email/password"

  - step: 2
    question: "What is the business value?"
    hint: "Why is this change important? What problem does it solve?"
    example: "Increase portal adoption by 25%"

  - step: 3
    question: "What are the acceptance criteria?"
    hint: "How will you know this is done correctly?"
    example: |
      - Login page with email/password fields
      - Integration with Auth0 SSO
      - Session management with 30-minute timeout

  - step: 4
    question: "What is the priority?"
    options: [critical, high, medium, low]
    default: medium

  - step: 5
    question: "What type of work is this?"
    options: [create, update, remediate, read, delete]
    hint: "I've analyzed your description and suggest: {suggested_work_type}"
    explanation: |
      - create: New capability
      - update: Change existing behavior
      - remediate: Fix production issue
      - read: Analyze or investigate
      - delete: Retire capability
```

### 4.2 Runtime Feedback → Intent Workflow

**Purpose**: Close the feedback loop from production to requirements (Methodology Section 10.0)

**Trigger**: Production incident, alert, or anomaly detected

**Steps**:

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Production Event Detected                                    │
│    - Error spike in monitoring                                  │
│    - Performance degradation                                    │
│    - User complaint                                             │
│    - Security alert                                             │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Runtime Feedback Agent Analyzes Event                        │
│    - Extract REQ-* keys from logs/metrics                       │
│    - Assess severity and impact                                 │
│    - Determine if intent generation is warranted                │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Generate Intent (if warranted)                               │
│    - Create intent with source: runtime_feedback                │
│    - Classification: remediate (high priority)                  │
│    - Include incident context (logs, metrics, REQ keys)         │
│    - Link to original requirements                              │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Human Review                                                  │
│    - Notify on-call engineer                                    │
│    - Review auto-generated intent                               │
│    - Approve, modify, or reject                                 │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Flow to SDLC                                                  │
│    - If approved: Enter Requirements stage                      │
│    - High priority intents bypass normal queue                  │
│    - Incident ID tracked through all stages                     │
└─────────────────────────────────────────────────────────────────┘
```

**Runtime Feedback Intent Schema**:

```yaml
id: INT-20251203-042

classification:
  work_type: remediate  # Always remediate for runtime feedback
  category: bug
  priority: critical | high  # Based on incident severity
  impact: high  # Runtime issues always high impact

title: "[INCIDENT-12345] Authentication timeout in production"

description: |
  AUTOMATICALLY GENERATED FROM RUNTIME FEEDBACK

  Incident ID: INCIDENT-12345
  Detected at: 2025-12-03T10:15:00Z
  Severity: P1 (Critical)

  Symptom:
  Authentication requests timing out after 30 seconds.
  Affected 1,247 users in 15-minute window.

  Traces to:
  - REQ-F-AUTH-001 (User login functionality)
  - REQ-NFR-PERF-001 (Login response < 500ms)

  Telemetry:
  - Error rate: 45% (baseline: 0.1%)
  - P95 latency: 30,000ms (baseline: 120ms)
  - Affected service: auth-service-prod

  Initial Hypothesis:
  Database connection pool exhaustion.

source:
  type: runtime_feedback
  author: "runtime-feedback-agent"
  timestamp: "2025-12-03T10:17:00Z"
  context: |
    Datadog alert: "auth-service error rate > 10%"
    Incident channel: #incident-12345
    On-call: john.doe@company.com

# Incident-specific fields
incident:
  id: INCIDENT-12345
  severity: P1
  started_at: "2025-12-03T10:15:00Z"
  resolved_at: null
  affected_users: 1247
  affected_requirements:
    - REQ-F-AUTH-001
    - REQ-NFR-PERF-001
  telemetry_links:
    - "https://datadog.com/dashboard/auth-service?from=..."
    - "https://sentry.io/issues/12345"
  postmortem_required: true

status: draft  # Awaits on-call review
```

### 4.3 Eco-Intent Generation Workflow

**Purpose**: Implements REQ-INTENT-003 for ecosystem monitoring

**Trigger**: Scheduled scan or webhook from ecosystem monitor

**Steps**:

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Ecosystem Monitor Detects Change                             │
│    - GitHub Security Advisory (webhook)                         │
│    - npm audit (daily cron)                                     │
│    - API changelog (RSS feed)                                   │
│    - Compliance scanner (weekly)                                │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Parse Ecosystem Event                                        │
│    - Extract event type (vulnerability, deprecation, etc.)     │
│    - Extract metadata (CVE, package, version, etc.)            │
│    - Assess severity and impact                                │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Check for Duplicate                                          │
│    - Search existing eco-intents                               │
│    - If duplicate: Update existing intent                      │
│    - If new: Proceed to generation                             │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Impact Assessment                                            │
│    - Scan project files for affected code                      │
│    - Check dependency tree                                     │
│    - Estimate effort to remediate                              │
│    - Assign priority based on impact                           │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Generate Eco-Intent                                          │
│    - Create INT-ECO-YYYYMMDD-NNN                               │
│    - Populate eco_intent_template.yml                          │
│    - Include impact assessment                                 │
│    - Set status: draft                                         │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. Human Review (Critical/High only)                            │
│    - Notify security team (critical)                           │
│    - Notify tech lead (high)                                   │
│    - Auto-approve medium/low after 24 hours                    │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. Update Intent Index                                          │
│    - Add entry to intent_index.yml                             │
│    - Update eco-intent statistics                              │
└─────────────────────────────────────────────────────────────────┘
```

**Ecosystem Monitor Integration**:

```yaml
# Configuration for ecosystem monitors
# File: .ai-workspace/config/ecosystem_monitors.yml

monitors:
  security_vulnerabilities:
    enabled: true
    sources:
      - type: github_advisory
        webhook_url: "https://api.github.com/repos/{owner}/{repo}/vulnerability-alerts"
        auth_token: "${GITHUB_TOKEN}"

      - type: npm_audit
        schedule: "0 8 * * *"  # Daily at 8am
        command: "npm audit --json"

      - type: snyk
        schedule: "0 9 * * MON"  # Weekly on Monday
        command: "snyk test --json"

    priority_rules:
      critical: ["cvss_score >= 9.0", "exploit_available = true"]
      high: ["cvss_score >= 7.0", "affected_files > 10"]
      medium: ["cvss_score >= 4.0"]
      low: ["cvss_score < 4.0"]

  deprecations:
    enabled: true
    sources:
      - type: nodejs_releases
        url: "https://nodejs.org/en/about/releases/"
        schedule: "0 10 * * MON"  # Weekly

      - type: package_deprecations
        schedule: "0 11 * * *"  # Daily
        command: "npm outdated --json"

    priority_rules:
      high: ["days_until_eol < 90"]
      medium: ["days_until_eol < 180"]
      low: ["days_until_eol >= 180"]

  api_changes:
    enabled: false  # Not implemented yet

  compliance_updates:
    enabled: false  # Not implemented yet
```

**Eco-Intent Notification Template**:

```markdown
# Eco-Intent Notification

**Priority**: {priority}
**Type**: {eco_event.type}
**Intent ID**: {id}

## Summary

{title}

## Impact Assessment

- **Affected Files**: {impact_assessment.affected_files | count}
- **Estimated Effort**: {impact_assessment.estimated_effort}
- **Risk Level**: {impact_assessment.risk_level}

## Details

{eco_event details}

## Recommended Action

{description}

## Review Required

Please review and approve this eco-intent:
{file_path}

---
Generated by Ecosystem Monitor at {source.timestamp}
```

---

## 5. Integration Points

### 5.1 Intent → Requirements Stage

**Purpose**: Flow approved intents to Requirements Agent

**Handoff Criteria**:
- Intent status: `approved`
- All required fields populated
- Classification complete

**Process**:

```
┌─────────────────────────────────────────────────────────────────┐
│ Intent Management                                               │
│                                                                 │
│ File: .ai-workspace/intents/human/INT-20251203-001.yml         │
│ Status: approved                                                │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ Requirements Agent Invoked                                      │
│                                                                 │
│ Command: /aisdlc-agent requirements INT-20251203-001           │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ Requirements Agent Reads Intent                                 │
│                                                                 │
│ - Parse intent YAML                                            │
│ - Extract title, description, acceptance criteria              │
│ - Understand work type and priority                            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ Requirements Agent Generates REQ-* Keys                         │
│                                                                 │
│ - REQ-F-AUTH-001: "User login with email/password"            │
│ - REQ-NFR-SEC-001: "Passwords hashed with bcrypt"             │
│ - REQ-NFR-PERF-001: "Login response < 500ms"                  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ Requirements Agent Updates Intent                               │
│                                                                 │
│ intent.derived_requirements = [                                │
│   "REQ-F-AUTH-001",                                            │
│   "REQ-NFR-SEC-001",                                           │
│   "REQ-NFR-PERF-001"                                           │
│ ]                                                              │
│ intent.lifecycle.requirements_stage.completed = timestamp      │
│ intent.status = "in_progress"                                  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ Requirements Agent Creates Requirement Files                    │
│                                                                 │
│ Files:                                                         │
│ - docs/requirements/REQ-F-AUTH-001.md                          │
│ - docs/requirements/REQ-NFR-SEC-001.md                         │
│ - docs/requirements/REQ-NFR-PERF-001.md                        │
└─────────────────────────────────────────────────────────────────┘
```

**Traceability**: Bidirectional links

```yaml
# Intent file references requirements
derived_requirements:
  - REQ-F-AUTH-001
  - REQ-NFR-SEC-001
  - REQ-NFR-PERF-001
```

```markdown
# Requirement file references intent

**Derived From**: INT-20251203-001
```

### 5.2 Runtime Feedback → Intent

**Purpose**: Close feedback loop from production (Methodology Section 10.0)

**Integration Architecture**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Production Environment                        │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Application │  │ Logs        │  │ Metrics     │            │
│  │ (REQ tags)  │→ │ (REQ tags)  │→ │ (REQ tags)  │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Observability Platform (Datadog, etc.)              │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Alert: "ERROR rate spike for REQ-F-AUTH-001"           │   │
│  │ Severity: P1                                           │   │
│  │ Affected: 1,247 users                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Runtime Feedback Agent (Stage 7)                    │
│                                                                 │
│  1. Receive alert webhook                                      │
│  2. Parse alert for REQ-* tags                                 │
│  3. Query telemetry for context                                │
│  4. Assess severity and impact                                 │
│  5. Generate intent (if warranted)                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Intent Management                             │
│                                                                 │
│  File: .ai-workspace/intents/human/INT-20251203-042.yml        │
│  Type: remediate                                               │
│  Source: runtime_feedback                                      │
│  Status: draft (awaits review)                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Human Review & Approval                      │
│                                                                 │
│  On-call engineer reviews auto-generated intent                │
│  Approves → Flows to Requirements stage                        │
│  Rejects → Intent archived with reason                         │
└─────────────────────────────────────────────────────────────────┘
```

**Code Example**: Runtime Feedback Agent

```python
# runtime_feedback_agent.py

def process_alert(alert: dict) -> Optional[str]:
    """
    Process production alert and generate intent if warranted.

    Args:
        alert: Alert payload from observability platform

    Returns:
        Intent ID if generated, None otherwise
    """
    # Extract REQ tags from alert
    req_tags = extract_req_tags(alert)

    if not req_tags:
        logger.info("Alert has no REQ tags, skipping intent generation")
        return None

    # Assess severity
    severity = assess_severity(alert)

    if severity not in ['P1', 'P2']:
        logger.info(f"Alert severity {severity} below threshold, skipping")
        return None

    # Query telemetry for context
    telemetry = query_telemetry(
        req_tags=req_tags,
        start_time=alert['start_time'],
        end_time=alert['end_time']
    )

    # Generate intent
    intent_id = generate_intent(
        work_type='remediate',
        priority='critical' if severity == 'P1' else 'high',
        title=f"[INCIDENT-{alert['incident_id']}] {alert['title']}",
        description=generate_description(alert, telemetry, req_tags),
        source={
            'type': 'runtime_feedback',
            'author': 'runtime-feedback-agent',
            'context': f"Incident: {alert['incident_id']}"
        },
        incident={
            'id': alert['incident_id'],
            'severity': severity,
            'affected_requirements': req_tags,
            'telemetry_links': telemetry['links']
        }
    )

    # Notify on-call
    notify_oncall(intent_id, alert)

    return intent_id
```

### 5.3 Ecosystem Monitor → Intent

**Purpose**: Auto-generate eco-intents from ecosystem changes

**Integration Architecture**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Ecosystem Sources                             │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ GitHub       │  │ npm audit    │  │ Snyk         │         │
│  │ Security     │  │              │  │              │         │
│  │ Advisory     │  │              │  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└──────┬────────────────┬────────────────┬────────────────────────┘
       │                │                │
       │ (webhook)      │ (cron)         │ (cron)
       │                │                │
       ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│              Ecosystem Monitor Service                           │
│                                                                 │
│  1. Receive/fetch ecosystem events                             │
│  2. Parse and normalize event data                             │
│  3. Assess impact on project                                   │
│  4. Generate eco-intent                                        │
│  5. Notify if critical/high priority                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Intent Management                             │
│                                                                 │
│  File: .ai-workspace/intents/eco/INT-ECO-20251203-001.yml      │
│  Type: remediate | update                                      │
│  Source: ecosystem_monitor                                     │
│  Status: draft (awaits review if high/critical)                │
└─────────────────────────────────────────────────────────────────┘
```

**Code Example**: Ecosystem Monitor

```python
# ecosystem_monitor.py

def process_security_advisory(advisory: dict) -> Optional[str]:
    """
    Process GitHub Security Advisory and generate eco-intent.

    Args:
        advisory: GitHub Advisory payload

    Returns:
        Eco-intent ID if generated, None otherwise
    """
    # Extract vulnerability details
    cve_id = advisory['cve_id']
    severity = advisory['severity']  # critical, high, medium, low
    affected_package = advisory['package']['name']
    affected_version = advisory['package']['ecosystem_specific']['affected']
    fixed_version = advisory['package']['ecosystem_specific']['fixed']

    # Check if project uses affected package
    impact = assess_package_impact(affected_package, affected_version)

    if not impact['is_affected']:
        logger.info(f"Project not affected by {cve_id}, skipping")
        return None

    # Determine priority
    priority_map = {
        'critical': 'critical',
        'high': 'high',
        'medium': 'medium',
        'low': 'low'
    }
    priority = priority_map[severity]

    # Generate eco-intent
    eco_intent_id = generate_eco_intent(
        work_type='remediate',
        priority=priority,
        title=f"[AUTO] Security vulnerability in {affected_package} ({cve_id})",
        description=generate_vulnerability_description(advisory, impact),
        eco_event={
            'type': 'security_vulnerability',
            'detected_at': datetime.now().isoformat(),
            'source': 'GitHub Security Advisory',
            'vulnerability': {
                'cve_id': cve_id,
                'severity': severity,
                'affected_package': affected_package,
                'fixed_version': fixed_version,
                'cwe_ids': advisory.get('cwe_ids', [])
            }
        },
        impact_assessment={
            'affected_files': impact['affected_files'],
            'affected_dependencies': impact['dependency_tree'],
            'estimated_effort': estimate_effort(impact),
            'risk_level': map_severity_to_risk(severity)
        }
    )

    # Notify if critical/high
    if priority in ['critical', 'high']:
        notify_security_team(eco_intent_id, advisory)

    return eco_intent_id
```

---

## 6. Validation

### 6.1 Required Fields Validation

**Purpose**: Ensure intents have minimum required information

**Validation Rules**:

```yaml
# Intent validation schema
# File: .ai-workspace/intents/intent_schema.json

{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["id", "classification", "title", "description", "source", "status"],
  "properties": {
    "id": {
      "type": "string",
      "pattern": "^INT(-ECO)?-[0-9]{8}-[0-9]{3}$",
      "description": "Unique intent identifier"
    },
    "classification": {
      "type": "object",
      "required": ["work_type", "category", "priority"],
      "properties": {
        "work_type": {
          "type": "string",
          "enum": ["create", "update", "remediate", "read", "delete"]
        },
        "category": {
          "type": "string",
          "enum": ["feature", "bug", "refactor", "documentation", "infrastructure", "security", "dependency"]
        },
        "priority": {
          "type": "string",
          "enum": ["critical", "high", "medium", "low"]
        },
        "impact": {
          "type": "string",
          "enum": ["high", "medium", "low"]
        }
      }
    },
    "title": {
      "type": "string",
      "minLength": 10,
      "maxLength": 200,
      "description": "Short descriptive title"
    },
    "description": {
      "type": "string",
      "minLength": 50,
      "description": "Detailed description with acceptance criteria"
    },
    "source": {
      "type": "object",
      "required": ["type", "author", "timestamp"],
      "properties": {
        "type": {
          "type": "string",
          "enum": ["human", "runtime_feedback", "ecosystem_monitor", "manual"]
        },
        "author": {
          "type": "string"
        },
        "timestamp": {
          "type": "string",
          "format": "date-time"
        }
      }
    },
    "status": {
      "type": "string",
      "enum": ["draft", "approved", "in_progress", "completed", "rejected", "blocked"]
    }
  },

  "if": {
    "properties": {
      "classification": {
        "properties": {
          "work_type": { "const": "remediate" }
        }
      }
    }
  },
  "then": {
    "required": ["incident"],
    "properties": {
      "incident": {
        "type": "object",
        "required": ["id", "severity"],
        "description": "Remediation intents must include incident details"
      }
    }
  }
}
```

**Validation Process**:

```python
# validate_intent.py

import json
import yaml
from jsonschema import validate, ValidationError

def validate_intent_file(intent_file_path: str) -> tuple[bool, list[str]]:
    """
    Validate intent file against schema.

    Args:
        intent_file_path: Path to intent YAML file

    Returns:
        Tuple of (is_valid, errors)
    """
    # Load schema
    with open('.ai-workspace/intents/intent_schema.json') as f:
        schema = json.load(f)

    # Load intent
    with open(intent_file_path) as f:
        intent = yaml.safe_load(f)

    # Validate
    errors = []
    try:
        validate(instance=intent, schema=schema)
    except ValidationError as e:
        errors.append(f"Schema validation failed: {e.message}")
        return False, errors

    # Custom business rules
    errors.extend(validate_business_rules(intent))

    return len(errors) == 0, errors

def validate_business_rules(intent: dict) -> list[str]:
    """
    Validate business rules not covered by JSON Schema.
    """
    errors = []

    # Rule: Description must include acceptance criteria for create/update
    if intent['classification']['work_type'] in ['create', 'update']:
        if 'acceptance criteria' not in intent['description'].lower():
            errors.append("Description must include acceptance criteria")

    # Rule: Remediate intents must reference incident ID
    if intent['classification']['work_type'] == 'remediate':
        if 'incident' not in intent:
            errors.append("Remediate intents must include incident details")

    # Rule: Critical intents require impact assessment
    if intent['classification']['priority'] == 'critical':
        if 'impact' not in intent['classification']:
            errors.append("Critical intents must include impact assessment")

    return errors
```

### 6.2 Key Uniqueness Enforcement

**Purpose**: Prevent duplicate intent IDs

**Strategy**: Atomic file creation

```python
# intent_key_manager.py

import os
from datetime import datetime
from pathlib import Path

def generate_unique_intent_id(
    workspace_path: str,
    is_eco_intent: bool = False
) -> str:
    """
    Generate unique intent ID with atomic collision detection.

    Args:
        workspace_path: Path to .ai-workspace directory
        is_eco_intent: True for eco-intents, False for human intents

    Returns:
        Unique intent ID

    Raises:
        RuntimeError: If unable to generate unique ID after retries
    """
    intents_dir = Path(workspace_path) / 'intents'
    subdir = 'eco' if is_eco_intent else 'human'

    today = datetime.now().strftime("%Y%m%d")
    prefix = "INT-ECO-" if is_eco_intent else "INT-"

    # Find highest existing counter for today
    pattern = f"{prefix}{today}-*.yml"
    existing_files = list((intents_dir / subdir).glob(pattern))

    if not existing_files:
        counter = 1
    else:
        counters = [
            int(f.stem.split('-')[-1])
            for f in existing_files
        ]
        counter = max(counters) + 1

    # Try to create file with exclusive lock (prevents collisions)
    max_attempts = 10
    for attempt in range(max_attempts):
        intent_id = f"{prefix}{today}-{counter:03d}"
        file_path = intents_dir / subdir / f"{intent_id}.yml"

        try:
            # Open with O_EXCL flag (fails if file exists)
            fd = os.open(file_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)

            # Success! File created atomically
            return intent_id

        except FileExistsError:
            # Collision - try next counter
            counter += 1
            continue

    raise RuntimeError(
        f"Unable to generate unique intent ID after {max_attempts} attempts"
    )
```

### 6.3 Classification Validation

**Purpose**: Ensure work type classification is correct

**Strategy**: LLM-assisted validation with human override

```python
# classify_intent.py

def classify_intent(description: str) -> dict:
    """
    Classify intent based on description.

    Args:
        description: Intent description text

    Returns:
        Classification dict with work_type, confidence, explanation
    """
    # Define classification indicators
    indicators = {
        'create': ['add', 'new', 'implement', 'build', 'create'],
        'update': ['change', 'modify', 'improve', 'enhance', 'refactor', 'update'],
        'remediate': ['fix', 'bug', 'incident', 'outage', 'error', 'failure', 'broken'],
        'read': ['analyze', 'investigate', 'research', 'explore', 'study'],
        'delete': ['remove', 'retire', 'deprecate', 'delete', 'decommission']
    }

    # Count indicator matches
    desc_lower = description.lower()
    scores = {}

    for work_type, keywords in indicators.items():
        score = sum(1 for keyword in keywords if keyword in desc_lower)
        if score > 0:
            scores[work_type] = score

    if not scores:
        return {
            'work_type': None,
            'confidence': 0.0,
            'explanation': "No clear indicators found. Please classify manually."
        }

    # Get highest scoring work type
    work_type = max(scores, key=scores.get)
    confidence = scores[work_type] / sum(scores.values())

    return {
        'work_type': work_type,
        'confidence': confidence,
        'explanation': f"Detected keywords: {', '.join([k for k in indicators[work_type] if k in desc_lower])}"
    }

def validate_classification(intent: dict) -> list[str]:
    """
    Validate that classification matches intent content.

    Args:
        intent: Intent dictionary

    Returns:
        List of validation warnings/errors
    """
    issues = []

    # Re-classify based on description
    auto_classification = classify_intent(intent['description'])

    # Warn if mismatch
    if auto_classification['work_type'] != intent['classification']['work_type']:
        issues.append(
            f"Classification mismatch: Declared as '{intent['classification']['work_type']}' "
            f"but description suggests '{auto_classification['work_type']}' "
            f"({auto_classification['explanation']})"
        )

    # Check for remediate-specific requirements
    if intent['classification']['work_type'] == 'remediate':
        if 'incident' not in intent:
            issues.append("Remediate intents must include incident details")

        if intent['classification']['priority'] not in ['critical', 'high']:
            issues.append("Remediate intents should typically be critical or high priority")

    return issues
```

---

## 7. Examples

### 7.1 Complete Human Intent Example

```yaml
# File: .ai-workspace/intents/human/INT-20251203-001.yml

# Intent identifier
id: INT-20251203-001

# Classification
classification:
  work_type: create
  category: feature
  priority: high
  impact: high
  effort_estimate: "2-5 days"

# Core fields
title: "Add user authentication to customer portal"
description: |
  Users need to log in with email/password to access the customer portal.
  Authentication should integrate with our existing Auth0 SSO provider.

  Business Context:
  Customer support reports indicate 40% of users abandon the portal due to
  lack of self-service authentication. This creates support ticket volume.

  Acceptance Criteria:
  - [ ] Login page with email/password fields
  - [ ] "Forgot password" link that sends reset email
  - [ ] Integration with Auth0 SSO provider
  - [ ] Session management with 30-minute idle timeout
  - [ ] "Remember me" checkbox for 7-day persistent sessions
  - [ ] Logout button visible on all authenticated pages
  - [ ] Redirect to originally requested page after login
  - [ ] Display error messages for invalid credentials
  - [ ] Rate limiting on login attempts (5 per minute)
  - [ ] HTTPS required for all auth endpoints

# Origin information
source:
  type: human
  author: "john.doe@company.com"
  timestamp: "2025-12-03T14:32:15Z"
  context: |
    Requested by Product Manager based on customer feedback analysis.
    Aligns with Q4 goal to increase portal self-service adoption by 30%.

# Status tracking
status: approved
status_history:
  - status: draft
    timestamp: "2025-12-03T14:32:15Z"
    author: "john.doe@company.com"
    comment: "Initial draft"
  - status: approved
    timestamp: "2025-12-03T15:10:22Z"
    author: "jane.smith@company.com"
    comment: "Approved by product owner. Prioritized for Sprint 23."

# Relationships
related_intents:
  - INT-20251120-015  # "Implement SSO integration" (prerequisite)
  - INT-20251201-008  # "Add session management framework"

derived_requirements:
  - REQ-F-AUTH-001
  - REQ-F-AUTH-002
  - REQ-F-AUTH-003
  - REQ-NFR-SEC-001
  - REQ-NFR-SEC-002
  - REQ-NFR-PERF-001
  - REQ-DATA-001

# Lifecycle tracking
lifecycle:
  requirements_stage:
    started: "2025-12-03T16:00:00Z"
    completed: "2025-12-03T17:30:00Z"
    agent: "AISDLC Requirements Agent"
    artifacts:
      - "docs/requirements/REQ-F-AUTH-001.md"
      - "docs/requirements/REQ-F-AUTH-002.md"
      - "docs/requirements/REQ-F-AUTH-003.md"
  design_stage:
    started: "2025-12-03T18:00:00Z"
    completed: null
    agent: "AISDLC Design Agent"
  tasks_stage:
    started: null
    completed: null
    agent: null
  code_stage:
    started: null
    completed: null
    agent: null
  system_test_stage:
    started: null
    completed: null
    agent: null
  uat_stage:
    started: null
    completed: null
    agent: null
  runtime_feedback_stage:
    started: null
    completed: null
    agent: null

# Custom metadata
metadata:
  business_value: "Increase portal adoption by 25%, reduce support tickets by 30%"
  customer_segment: "enterprise"
  compliance: ["SOC2", "GDPR", "PCI-DSS"]
  tags: ["security", "authentication", "portal", "auth0", "sso"]
  stakeholders:
    product_owner: "jane.smith@company.com"
    tech_lead: "bob.jones@company.com"
    security_reviewer: "alice.security@company.com"

# Version tracking
version: 2
created_at: "2025-12-03T14:32:15Z"
updated_at: "2025-12-03T17:30:00Z"
```

### 7.2 Complete Eco-Intent Example (Security Vulnerability)

```yaml
# File: .ai-workspace/intents/eco/INT-ECO-20251203-001.yml

# Eco-intent identifier
id: INT-ECO-20251203-001

# Classification (automatically assigned)
classification:
  work_type: remediate
  category: security
  priority: critical
  impact: high
  effort_estimate: "1-2 days"

# Eco-specific fields
eco_event:
  type: security_vulnerability
  detected_at: "2025-12-03T08:00:00Z"
  source: "GitHub Security Advisory"

  vulnerability:
    cve_id: "CVE-2025-12345"
    severity: critical
    cvss_score: 9.8
    affected_package: "express@4.17.1"
    fixed_version: "4.18.2"
    cwe_ids: ["CWE-79"]
    description: |
      Cross-Site Scripting (XSS) vulnerability in Express.js allows
      remote attackers to inject arbitrary web script or HTML via
      crafted URL parameters in error handler middleware.
    exploit_available: true
    exploit_public: true
    references:
      - "https://github.com/advisories/GHSA-xxxx-yyyy-zzzz"
      - "https://nvd.nist.gov/vuln/detail/CVE-2025-12345"

# Impact assessment (auto-generated)
impact_assessment:
  affected_files:
    - "src/server.js"
    - "src/api/routes.js"
    - "src/middleware/errorHandler.js"
  affected_dependencies:
    - "express@4.17.1"
    - "body-parser@1.19.0 (depends on express)"
  dependency_tree:
    express:
      version: "4.17.1"
      used_by:
        - "src/server.js"
        - "src/api/routes.js"
      transitive_dependencies: 31
  estimated_effort: "1-2 days"
  risk_level: high
  mitigation_complexity: low
  breaking_changes: false

# Standard intent fields
title: "[AUTO] CRITICAL: XSS vulnerability in express@4.17.1 (CVE-2025-12345)"
description: |
  ⚠️ AUTOMATICALLY GENERATED ECO-INTENT - REQUIRES IMMEDIATE ATTENTION

  ## Vulnerability Summary

  A critical security vulnerability (CVE-2025-12345) has been detected
  in express@4.17.1. This package is used in 3 files across the project.

  **Severity**: CRITICAL (CVSS: 9.8)
  **CWE**: CWE-79 (Cross-Site Scripting)
  **Exploit Status**: Public exploit available

  ## Attack Vector

  Remote attackers can inject arbitrary JavaScript code via crafted URL
  parameters in error handler middleware. This allows:
  - Session hijacking
  - Credential theft
  - Defacement
  - Phishing attacks

  ## Affected Components

  - `src/server.js` - Main server initialization
  - `src/api/routes.js` - API route handlers
  - `src/middleware/errorHandler.js` - Custom error handler

  ## Recommended Action

  1. **IMMEDIATE**: Upgrade express from 4.17.1 to 4.18.2
  2. Review all error handlers for XSS vulnerabilities
  3. Run security regression tests
  4. Deploy to production within 24 hours

  ## Migration Steps

  ```bash
  # Update package.json
  npm install express@4.18.2

  # Run tests
  npm test

  # Security audit
  npm audit
  ```

  ## Acceptance Criteria

  - [ ] express upgraded to 4.18.2
  - [ ] All tests pass
  - [ ] npm audit shows no critical vulnerabilities
  - [ ] Error handlers sanitize user input
  - [ ] Security regression tests added
  - [ ] Deployed to production

source:
  type: ecosystem_monitor
  author: "ecosystem-monitor-service"
  timestamp: "2025-12-03T08:00:00Z"
  context: |
    Detected by GitHub Security Advisory scanner (daily scan at 8am).
    Notification sent to security team.

# Status tracking
status: draft
status_history:
  - status: draft
    timestamp: "2025-12-03T08:00:00Z"
    author: "ecosystem-monitor-service"
    comment: "Auto-generated from security advisory. Awaiting security team review."

# Relationships
related_intents: []
derived_requirements: []

# Lifecycle tracking
lifecycle:
  requirements_stage:
    started: null
    completed: null
    agent: null
  # ... (other stages)

# Custom metadata
metadata:
  business_value: "Prevent security breach, protect customer data, maintain compliance"
  compliance: ["SOC2", "PCI-DSS", "GDPR"]
  tags: ["security", "vulnerability", "express", "xss", "cve"]
  stakeholders:
    security_team: "security@company.com"
    on_call: "oncall@company.com"
  notification_sent:
    - "security@company.com"
    - "oncall@company.com"
  sla:
    response_time: "4 hours"
    resolution_time: "24 hours"

# Version tracking
version: 1
created_at: "2025-12-03T08:00:00Z"
updated_at: "2025-12-03T08:00:00Z"
```

### 7.3 Complete Eco-Intent Example (Deprecation)

```yaml
# File: .ai-workspace/intents/eco/INT-ECO-20251203-002.yml

id: INT-ECO-20251203-002

classification:
  work_type: update
  category: infrastructure
  priority: medium
  impact: medium
  effort_estimate: "3-5 days"

eco_event:
  type: deprecation
  detected_at: "2025-12-03T09:00:00Z"
  source: "Node.js Release Schedule"

  deprecation:
    deprecated_feature: "Node.js 16"
    current_version: "16.20.2"
    deprecation_date: "2023-10-24"
    end_of_life_date: "2024-04-30"
    days_until_eol: -217  # Already EOL!
    replacement: "Node.js 20 LTS"
    migration_guide_url: "https://nodejs.org/en/blog/announcements/v20-release-announce"
    breaking_changes:
      - "OpenSSL 3.x (breaking for some crypto operations)"
      - "V8 11.3 (may affect some native addons)"
      - "npm 9.x (lockfile format change)"

impact_assessment:
  affected_files:
    - ".nvmrc"
    - "package.json"
    - "Dockerfile"
    - ".github/workflows/ci.yml"
  affected_dependencies: []
  estimated_effort: "3-5 days"
  risk_level: medium
  mitigation_complexity: medium
  breaking_changes: true

title: "[AUTO] Node.js 16 is EOL - Upgrade to Node.js 20"
description: |
  ⚠️ AUTOMATICALLY GENERATED ECO-INTENT

  ## Deprecation Summary

  Node.js 16 reached End-of-Life on 2024-04-30 and is no longer receiving
  security updates. The project is currently 217 days past EOL.

  **Current Version**: Node.js 16.20.2
  **Recommended Version**: Node.js 20 LTS
  **EOL Date**: 2024-04-30 (217 days ago)
  **Risk**: Security vulnerabilities will not be patched

  ## Migration Path

  Node.js 20 is the current LTS release with support until 2026-04-30.

  ### Breaking Changes to Address

  1. **OpenSSL 3.x**: Some crypto operations may behave differently
  2. **V8 11.3**: Native addons may need recompilation
  3. **npm 9.x**: Lockfile format change (regenerate package-lock.json)

  ### Affected Files

  - `.nvmrc` - Update to `20`
  - `package.json` - Update `engines.node` to `>=20.0.0`
  - `Dockerfile` - Update base image to `node:20-alpine`
  - `.github/workflows/ci.yml` - Update actions/setup-node to node-version: 20

  ## Migration Steps

  ```bash
  # 1. Update local Node.js version
  nvm install 20
  nvm use 20

  # 2. Update project files
  echo "20" > .nvmrc

  # 3. Regenerate lockfile
  rm package-lock.json
  npm install

  # 4. Run tests
  npm test

  # 5. Update CI/CD
  # Edit .github/workflows/ci.yml, Dockerfile, etc.

  # 6. Test in staging environment
  # Deploy and validate
  ```

  ## Acceptance Criteria

  - [ ] .nvmrc updated to `20`
  - [ ] package.json engines.node updated to `>=20.0.0`
  - [ ] Dockerfile base image updated to `node:20-alpine`
  - [ ] CI workflows updated to use Node.js 20
  - [ ] package-lock.json regenerated
  - [ ] All tests pass on Node.js 20
  - [ ] No deprecation warnings in logs
  - [ ] Staging deployment successful
  - [ ] Production deployment successful

source:
  type: ecosystem_monitor
  author: "ecosystem-monitor-service"
  timestamp: "2025-12-03T09:00:00Z"
  context: |
    Detected by Node.js release schedule monitor (weekly check).
    Project is 217 days past Node.js 16 EOL.

status: draft

related_intents: []
derived_requirements: []

lifecycle:
  requirements_stage:
    started: null
    completed: null
  # ... (other stages)

metadata:
  business_value: "Maintain security posture, access latest Node.js features"
  compliance: ["SOC2"]
  tags: ["infrastructure", "nodejs", "deprecation", "upgrade"]
  stakeholders:
    devops_team: "devops@company.com"
    tech_lead: "techlead@company.com"
  timeline:
    target_completion: "2025-12-31"
    milestone: "Q4 Infrastructure Upgrades"

version: 1
created_at: "2025-12-03T09:00:00Z"
updated_at: "2025-12-03T09:00:00Z"
```

### 7.4 Runtime Feedback Intent Example

```yaml
# File: .ai-workspace/intents/human/INT-20251203-042.yml

id: INT-20251203-042

classification:
  work_type: remediate
  category: bug
  priority: critical
  impact: high
  effort_estimate: "1-3 days"

title: "[INCIDENT-12345] Authentication timeout in production"

description: |
  🚨 AUTOMATICALLY GENERATED FROM RUNTIME FEEDBACK

  ## Incident Summary

  **Incident ID**: INCIDENT-12345
  **Detected at**: 2025-12-03T10:15:00Z
  **Severity**: P1 (Critical)
  **Status**: ONGOING

  Authentication requests began timing out after 30 seconds.
  Affected 1,247 users in a 15-minute window.

  ## Symptom

  Users unable to log in to customer portal. Login requests hang
  for 30 seconds then return 504 Gateway Timeout.

  ## Traces to Requirements

  This incident affects the following requirements:
  - **REQ-F-AUTH-001**: User login functionality
  - **REQ-NFR-PERF-001**: Login response < 500ms (SLA violated)

  ## Telemetry

  - **Error Rate**: 45% (baseline: 0.1%)
  - **P95 Latency**: 30,000ms (baseline: 120ms)
  - **P99 Latency**: 30,000ms (baseline: 250ms)
  - **Affected Service**: auth-service-prod
  - **Affected Endpoints**: POST /api/v1/auth/login
  - **Affected Users**: 1,247 unique users
  - **Geographic Distribution**: US-East region only

  ## Initial Hypothesis

  Database connection pool exhaustion in auth-service.

  Evidence:
  - Database connection pool metrics show 100% utilization
  - Connection wait queue depth: 50+ (normal: 0-2)
  - Database CPU: 15% (not saturated)
  - Database connections: 100/100 (max pool size)

  ## Root Cause Analysis (Preliminary)

  Recent code deploy (v2.3.1) introduced long-running transaction
  in login flow that holds database connection for entire duration
  of Auth0 SSO validation (network call).

  Normally:
  1. Get connection
  2. Query user
  3. Release connection
  4. Call Auth0 (network I/O)
  5. Get connection
  6. Update session
  7. Release connection

  After v2.3.1:
  1. Get connection
  2. Query user
  3. Call Auth0 (network I/O) ← WHILE HOLDING CONNECTION
  4. Update session
  5. Release connection

  This causes connection pool starvation under load.

  ## Recommended Action

  1. **IMMEDIATE**: Rollback to v2.3.0
  2. **SHORT-TERM**: Fix v2.3.1 to release connection before Auth0 call
  3. **LONG-TERM**: Add connection pool monitoring alerts

  ## Acceptance Criteria

  - [ ] Root cause confirmed via code review
  - [ ] Fix implemented (release connection before external calls)
  - [ ] Unit tests added for connection pool management
  - [ ] Integration tests added for high-concurrency login scenarios
  - [ ] Connection pool monitoring alerts configured
  - [ ] Deployed to staging and validated
  - [ ] Deployed to production and validated
  - [ ] Postmortem document created
  - [ ] Runbook updated with this failure mode

source:
  type: runtime_feedback
  author: "runtime-feedback-agent"
  timestamp: "2025-12-03T10:17:00Z"
  context: |
    Triggered by Datadog alert: "auth-service error rate > 10%"

    Incident Channel: #incident-12345
    On-call: john.doe@company.com
    War Room: https://zoom.us/j/incident-12345

status: approved

incident:
  id: INCIDENT-12345
  severity: P1
  started_at: "2025-12-03T10:15:00Z"
  resolved_at: null
  affected_users: 1247
  affected_region: "us-east-1"
  affected_requirements:
    - REQ-F-AUTH-001
    - REQ-NFR-PERF-001
  suspected_root_cause: "Database connection pool exhaustion"
  suspected_trigger: "Deploy v2.3.1 at 2025-12-03T09:45:00Z"
  telemetry_links:
    - "https://app.datadoghq.com/dashboard/auth-service?from_ts=1733218500000"
    - "https://sentry.io/issues/12345"
    - "https://grafana.company.com/d/auth-service"
  communication:
    status_page: "https://status.company.com/incidents/12345"
    slack_channel: "#incident-12345"
    zoom_room: "https://zoom.us/j/incident-12345"
  postmortem_required: true
  sla_violated: true
  customer_impact: "High - 1,247 users unable to log in"

related_intents:
  - INT-20251203-001  # Original feature intent

derived_requirements: []

lifecycle:
  requirements_stage:
    started: "2025-12-03T10:20:00Z"
    completed: null
  # ... (other stages)

metadata:
  business_value: "Restore login functionality, prevent revenue loss"
  compliance: ["SOC2", "SLA"]
  tags: ["incident", "p1", "authentication", "database", "connection-pool"]
  stakeholders:
    on_call: "john.doe@company.com"
    incident_commander: "alice.manager@company.com"
    customer_support: "support@company.com"
  sla:
    response_time: "15 minutes"
    resolution_time: "4 hours"
  timeline:
    incident_detected: "2025-12-03T10:15:00Z"
    intent_created: "2025-12-03T10:17:00Z"
    on_call_notified: "2025-12-03T10:17:30Z"
    war_room_started: "2025-12-03T10:20:00Z"
    rollback_initiated: "2025-12-03T10:25:00Z"
    service_restored: "2025-12-03T10:32:00Z"

version: 1
created_at: "2025-12-03T10:17:00Z"
updated_at: "2025-12-03T10:32:00Z"
```

---

## 8. Implementation Guidance

### 8.1 Phase 1: Core Infrastructure (Week 1)

**Goal**: Implement basic intent capture and storage

**Tasks**:
1. Create directory structure (`.ai-workspace/intents/`)
2. Define intent schema (YAML format)
3. Implement intent key generation algorithm
4. Create intent templates
5. Implement file-based storage
6. Write unit tests

**Deliverables**:
- `.ai-workspace/intents/` directory structure
- `intent_schema.json` (JSON Schema)
- `intent_template.yml`
- `intent_key_manager.py` (ID generation)
- `validate_intent.py` (validation)
- Unit tests (90%+ coverage)

### 8.2 Phase 2: Human Intent Workflow (Week 2)

**Goal**: Enable human intent capture via slash command

**Tasks**:
1. Create `/aisdlc-create-intent` command
2. Implement interactive prompts
3. Implement classification logic
4. Implement intent index
5. Add git integration
6. Create command tests

**Deliverables**:
- `.claude/commands/aisdlc-create-intent.md`
- Interactive prompt script
- `classify_intent.py`
- `intent_index.yml` (auto-generated)
- Git commit templates
- Integration tests

### 8.3 Phase 3: Eco-Intent Generation (Week 3)

**Goal**: Auto-generate intents from ecosystem changes

**Tasks**:
1. Implement ecosystem monitor service
2. Integrate GitHub Security Advisories
3. Integrate npm audit
4. Implement impact assessment
5. Implement notification system
6. Create monitor tests

**Deliverables**:
- `ecosystem_monitor.py`
- `ecosystem_monitors.yml` (config)
- GitHub webhook handler
- npm audit integration
- Email/Slack notifications
- Integration tests

### 8.4 Phase 4: Runtime Feedback Integration (Week 4)

**Goal**: Close feedback loop from production

**Tasks**:
1. Implement runtime feedback agent
2. Integrate with observability platform (Datadog)
3. Implement REQ-* tag extraction
4. Implement auto-intent generation
5. Create incident intent template
6. Create runtime feedback tests

**Deliverables**:
- `runtime_feedback_agent.py`
- Datadog webhook handler
- REQ tag extraction logic
- `incident_intent_template.yml`
- Alert routing configuration
- Integration tests

### 8.5 Phase 5: Requirements Stage Integration (Week 5)

**Goal**: Flow intents to Requirements Agent

**Tasks**:
1. Implement intent → requirements handoff
2. Update Requirements Agent to read intents
3. Implement bidirectional linking
4. Update lifecycle tracking
5. Create integration tests
6. Update documentation

**Deliverables**:
- Intent handoff logic
- Requirements Agent updates
- Traceability matrix updates
- Lifecycle tracking code
- Integration tests
- Updated documentation

### 8.6 Testing Strategy

**Unit Tests**:
- Intent key generation (uniqueness, format)
- Intent validation (required fields, business rules)
- Classification logic (work type detection)
- Impact assessment (affected files)

**Integration Tests**:
- Full human intent capture workflow
- Eco-intent generation from mock events
- Runtime feedback intent generation
- Intent → Requirements handoff

**End-to-End Tests**:
- Create human intent → Requirements → Design
- Security advisory → Eco-intent → Requirements
- Production incident → Runtime intent → Remediation

**Performance Tests**:
- Generate 1,000 intents (unique IDs)
- Parse 10,000 intents (index performance)
- Concurrent intent creation (collision handling)

### 8.7 Monitoring and Observability

**Metrics to Track**:
- Intent creation rate (per day)
- Intent classification distribution (create/update/remediate)
- Intent status distribution (draft/approved/completed)
- Eco-intent generation rate
- Runtime feedback intent rate
- Intent → Requirements conversion time
- Intent lifecycle duration (creation → completion)

**Dashboards**:
- Intent funnel (draft → approved → completed)
- Eco-intent response times
- Runtime feedback loop performance
- Classification accuracy (manual overrides)

**Alerts**:
- Critical eco-intent not reviewed within 4 hours
- Runtime feedback intent not reviewed within 15 minutes
- Intent lifecycle stalled (no progress in 7 days)
- Intent index update failures

### 8.8 Documentation Requirements

**User Documentation**:
- How to create an intent
- How to classify intents
- How to review eco-intents
- How to respond to runtime feedback intents

**Developer Documentation**:
- Intent schema specification
- Intent key generation algorithm
- Classification taxonomy
- Integration guide (Requirements, Runtime Feedback, Ecosystem Monitor)
- API reference (if programmatic access added)

**Operational Documentation**:
- Intent archival policy
- Ecosystem monitor configuration
- Alert routing configuration
- Disaster recovery (intent data loss)

---

## 9. Future Enhancements

### 9.1 Intent Approval Workflow

**Current**: Intents manually approved by changing status
**Future**: Formal approval workflow with roles (creator, reviewer, approver)

### 9.2 Intent Templates

**Current**: Single generic template
**Future**: Work type-specific templates (feature, bug, refactor, etc.)

### 9.3 Intent Dependencies

**Current**: `related_intents` as free-form list
**Future**: Formal dependency graph with `depends_on` and `blocks`

### 9.4 Intent Analytics

**Current**: Basic statistics in index
**Future**: Rich analytics dashboard (velocity, cycle time, classification accuracy)

### 9.5 Intent Search

**Current**: File system search
**Future**: Full-text search with filters (work type, status, date range)

### 9.6 Intent API

**Current**: File-based only
**Future**: REST API for programmatic access

### 9.7 Intent Webhooks

**Current**: No external notifications
**Future**: Webhooks for intent lifecycle events (created, approved, completed)

---

## 10. Appendix

### 10.1 Glossary

| Term | Definition |
|------|------------|
| Intent | A desire for change that drives the SDLC |
| INT-* | Intent key format (INT-YYYYMMDD-NNN) |
| Work Type | Classification of intent (create, update, remediate, read, delete) |
| Eco-Intent | Intent generated from ecosystem monitoring |
| Runtime Feedback Intent | Intent generated from production incidents |
| Control Regime | Set of quality gates and processes based on work type |

### 10.2 References

| Document | Section | Description |
|----------|---------|-------------|
| [ai_sdlc_method.md](../../ai_sdlc_method.md) | Section 2.3 | Intent concept and rationale |
| [ai_sdlc_method.md](../../ai_sdlc_method.md) | Section 2.4 | Work type classification |
| [ai_sdlc_method.md](../../ai_sdlc_method.md) | Section 10.0 | Runtime Feedback stage |
| [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) | Section 1 | Intent management requirements |
| [ADR-005](adrs/ADR-005-iterative-refinement-feedback-loops.md) | - | Feedback loop patterns |

### 10.3 Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-03 | Design Agent | Initial design document |

---

**Document Status**: Draft
**Next Review Date**: 2025-12-10
**Reviewers**: Requirements Agent, Tasks Agent, Code Agent

---

**Traceability Matrix**:

| Requirement | Design Section | Status |
|-------------|----------------|--------|
| REQ-INTENT-001 | 2.1, 4.1 | ✅ Implemented |
| REQ-INTENT-002 | 2.3, 4.1, 6.3 | ✅ Implemented |
| REQ-INTENT-003 | 2.4, 4.3, 5.3 | ✅ Implemented |

---

**Implementation Checklist**:

- [ ] Phase 1: Core Infrastructure (Week 1)
- [ ] Phase 2: Human Intent Workflow (Week 2)
- [ ] Phase 3: Eco-Intent Generation (Week 3)
- [ ] Phase 4: Runtime Feedback Integration (Week 4)
- [ ] Phase 5: Requirements Stage Integration (Week 5)
- [ ] Unit tests (90%+ coverage)
- [ ] Integration tests
- [ ] End-to-end tests
- [ ] Documentation complete
- [ ] Architecture review approved
- [ ] Security review approved
