# AI SDLC Methodology - Concept Inventory

**Purpose**: Exhaustive, terse checklist of all concepts defining the AI SDLC methodology
**Audience**: New Claude sessions, methodology auditors, concept completeness verification
**Version**: 1.2
**Date**: 2025-11-20

**Use Cases**:
- ✅ Audit: Ensure no concepts lost during updates
- ✅ Onboarding: Quick concept overview for new sessions
- ✅ Validation: Verify methodology completeness
- ✅ Evolution: Track new concept additions over time

---

## 1. Core Philosophy

### 1.1 Intent-Driven Development
- All work originates from observed intent (not backlogs or arbitrary tasks)
- Intent = mismatch between expected vs actual reality
- Intent classification: CRUD (Create, Update, Remediation, Read, Delete)
- Intent Manager: Central registry for all intent

### 1.2 AI-Augmented (Not AI-Driven)
- Humans decide, AI accelerates
- Humans remain accountable, AI suggests
- AI agents work alongside humans at each stage
- Human-in-the-loop for all critical decisions

### 1.3 Requirements as Control System (Homeostasis Model)
- Requirements = target state (like thermostat setpoint)
- Observer monitors runtime behavior
- Evaluator compares actual vs target
- Deviations generate new intent
- System self-corrects via feedback loop

### 1.4 Ecosystem-Aware Development
- Ecosystem E(t) = external operating environment at time t
- E(t) is **given** (external reality), not **chosen** (design decision)
- All decisions = f(Intent, E(t))
- Acknowledge strategic constraints, don't enumerate all dependencies

### 1.5 Continuous Feedback Loop
- Production behavior → Observer → Evaluator → Intent → SDLC
- Bidirectional traceability (forward: intent→runtime, backward: runtime→intent)
- Living requirements (evolve based on feedback)

---

## 2. The 7-Stage AI SDLC

### 2.1 Requirements Stage
- **Purpose**: Transform intent into structured, traceable requirements
- **Personas**: Product Owner, Business Analyst, Data Analyst
- **Inputs**: Raw intent from Intent Manager
- **Outputs**:
  - REQ-F-* (functional requirements)
  - REQ-NFR-* (non-functional requirements: performance, security, scalability)
  - REQ-DATA-* (data quality: completeness, accuracy, lineage, PII)
  - REQ-BR-* (business rules)
  - BDD scenarios (Given/When/Then)
- **Quality Gates**: All requirements have unique immutable keys, acceptance criteria
- **Key Concept**: Requirement keys are the golden thread

### 2.2 Design Stage
- **Purpose**: Transform requirements into technical solution
- **Personas**: Tech Lead, Architect, Data Architect
- **Inputs**: Requirements + BDD scenarios
- **Outputs**:
  - Component design (service boundaries, interactions)
  - Data models (ERDs, schemas)
  - API specifications (OpenAPI, GraphQL)
  - ADRs (Architecture Decision Records) - **acknowledging E(t)**
  - Data flow diagrams
  - Traceability matrix (design → REQ keys)
- **Quality Gates**: All components mapped to REQ keys, ADRs for strategic decisions
- **Key Concept**: ADRs document decisions **given** E(t) constraints

### 2.3 Tasks Stage
- **Purpose**: Break design into actionable work items
- **Personas**: Product Owner, Tech Lead
- **Inputs**: Design assets
- **Outputs**:
  - Epics (high-level features)
  - User stories (implementation tickets)
  - Data tasks (pipeline/schema tickets)
  - All tickets tagged with REQ keys
- **Quality Gates**: All tasks linked to REQ keys, dependencies identified
- **Key Concept**: Jira/Trello workflow integration

### 2.4 Code Stage
- **Purpose**: Implement work units using TDD
- **Personas**: Developers, Data Engineers
- **Inputs**: Tasks + Design
- **Outputs**:
  - Application code (tagged with REQ-F-*)
  - Unit tests (≥80% coverage, critical paths 100%)
  - Data pipelines (tagged with REQ-DATA-*)
  - Infrastructure-as-code (tagged with REQ-NFR-*)
- **Quality Gates**: TDD followed (RED→GREEN→REFACTOR), Key Principles compliance
- **Key Concept**: TDD workflow is mandatory

### 2.5 System Test Stage
- **Purpose**: Verify integrated system with BDD
- **Personas**: QA Engineer, Data Quality Engineer
- **Inputs**: Code + BDD scenarios from Requirements
- **Outputs**:
  - BDD feature files (Gherkin: Given/When/Then)
  - Step definitions (automated tests)
  - Coverage matrix (REQ → scenarios)
  - Test results
- **Quality Gates**: Requirement coverage ≥95%, all scenarios pass
- **Key Concept**: BDD validates requirements end-to-end

### 2.6 UAT Stage
- **Purpose**: Business validation and sign-off
- **Personas**: Business SME, Data Steward
- **Inputs**: System test passed + acceptance criteria
- **Outputs**:
  - Manual UAT test cases
  - Automated UAT tests (BDD in business language)
  - Business sign-off
  - UAT results (tagged with REQ keys)
- **Quality Gates**: All critical scenarios pass, stakeholder approval
- **Key Concept**: Pure business language (no technical jargon)

### 2.7 Runtime Feedback Stage
- **Purpose**: Close feedback loop from production
- **Personas**: DevOps, SRE, Data Engineers
- **Inputs**: Deployed system
- **Outputs**:
  - Release manifests (listing REQ keys)
  - Runtime telemetry (tagged with REQ keys)
  - Alerts (routed to Intent Manager)
  - New intent (deviations, Eco-Intent)
- **Quality Gates**: Telemetry tagged with REQ keys, SLA monitoring
- **Key Concept**: Telemetry must tag REQ keys for traceability

---

## 3. Requirement Traceability

### 3.1 Requirement Key Format
- **Structure**: `REQ-{TYPE}-{DOMAIN}-{SEQUENCE}`
- **Types**: F (functional), NFR (non-functional), DATA (data quality), BR (business rule)
- **Examples**: REQ-F-AUTH-001, REQ-NFR-PERF-001, REQ-DATA-CQ-001
- **Properties**: Unique, immutable, human-readable

### 3.2 The Golden Thread
- **Forward**: Intent → REQ → Design → Code → Tests → UAT → Deploy → Runtime
- **Backward**: Runtime issue → Code → Requirement → Intent
- **Tagging**: Every asset tagged with REQ keys (code comments, test names, logs, metrics)

### 3.3 Traceability Matrix
- **Purpose**: Map requirements to all downstream assets
- **Columns**: REQ key, Design component, Jira ticket, Code file, Test, UAT case, Runtime metric
- **Use**: Impact analysis, coverage verification, root cause analysis

---

## 4. Ecosystem Concepts

### 4.1 Ecosystem Constraint Vector E(t)
- **Definition**: External operating environment at time t
- **Components**:
  - runtime_platforms(t) - Python 3.11, Node 20, Java 17
  - cloud_providers(t) - AWS, GCP, Azure
  - available_apis(t) - OpenAI, Stripe, Auth0, Twilio
  - library_ecosystems(t) - npm, PyPI, Maven
  - compliance_reqs(t) - GDPR, HIPAA, SOC2, PCI-DSS
  - cost_landscape(t) - Pricing models, budget constraints
  - team_capabilities(t) - Skills, experience, preferences
- **Key Principle**: Given, not chosen (external reality)

### 4.2 Eco-Intent
- **Definition**: Automated intent generated by ecosystem E(t) changes
- **Sources**:
  - Security vulnerabilities (CVE alerts → upgrade intents)
  - API deprecations (EOL notices → migration intents)
  - Cost alerts (budget thresholds → optimization intents)
  - Compliance changes (new regulations → implementation intents)
  - Performance degradation (external API slow → caching intents)
- **Flow**: E(t) change → Monitor → Eco-Intent → Intent Manager → SDLC

### 4.3 Architecture Decision Records (ADRs)
- **Purpose**: Document strategic tech decisions acknowledging E(t)
- **When**: Cloud provider, language/framework, database, auth approach selections
- **Structure**:
  - Context: Requirements + Ecosystem constraints
  - Decision: Selected option + rejected alternatives
  - Ecosystem Constraints Acknowledged: Team, timeline, budget, compliance
  - Constraints Imposed Downstream: What Code/Runtime must use
- **Key Principle**: "Given E(t), we chose X" (not "we chose X")

### 4.4 Acknowledge vs Enumerate
- **Acknowledge**: Document strategic constraints (ADRs for major decisions)
- **Enumerate**: List all dependencies (tools handle this: package.json, requirements.txt)
- **Rule**: Don't recreate package managers, acknowledge what matters

---

## 5. Development Methodologies

### 5.1 Test-Driven Development (TDD)
- **Workflow**: RED → GREEN → REFACTOR → COMMIT
- **RED**: Write failing test first (before any code)
- **GREEN**: Write minimal code to pass test
- **REFACTOR**: Improve code quality (tests still pass)
- **COMMIT**: Save with REQ keys in commit message
- **Mandate**: No code without tests

### 5.2 Behavior-Driven Development (BDD)
- **Structure**: Given/When/Then
- **System Test**: Technical BDD (integration, service-to-service)
- **UAT**: Business BDD (pure business language, no tech jargon)
- **Gherkin**: Feature files with scenarios
- **Validation**: Each REQ must have ≥1 BDD scenario

### 5.3 Key Principles (Code Stage)
1. **Test Driven Development** - "No code without tests"
2. **Fail Fast & Root Cause** - "Break loudly, fix completely"
3. **Modular & Maintainable** - "Single responsibility, loose coupling"
4. **Reuse Before Build** - "Check first, create second"
5. **Open Source First** - "Suggest alternatives, human decides"
6. **No Legacy Baggage** - "Clean slate, no debt" (evolvable per context)
7. **Perfectionist Excellence** - "Best of breed only"
- **Ultimate Mantra**: "Excellence or nothing" 🔥
- **Evolution**: Principles can adapt per project context (document changes)

---

## 6. Context Framework

### 6.1 Context Definition
- **Purpose**: Explicit, versioned constraints/templates/knowledge guiding synthesis
- **Storage**: ai_sdlc_method repository
- **Types**:
  - Architecture context (tech stack, platforms, standards, patterns)
  - Data architecture context (models, schemas, lineage, retention)
  - Coding standards (style, security, naming)
  - Domain context (business rules, terminology)

### 6.2 Context Configuration Schema
- **Format**: YAML hierarchy
- **Layers**: Corporate → Division → Team → Project (federated)
- **Composability**: Contexts merge and override
- **Versioning**: Git-tracked, tagged releases

---

## 7. AI Agent Concepts

### 7.1 Agent Roles (One Per Stage)
- **Requirements Agent**: Generate structured requirements from intent
- **Design Agent**: Propose component design, check NFR compliance
- **Tasks Agent**: Break design into work items
- **Code Agent** (Developer Agent): Implement TDD, follow Key Principles
- **System Test Agent** (QA Agent): Create BDD tests, validate requirements
- **UAT Agent**: Generate business-language tests, validate acceptance
- **Runtime Feedback Agent**: Monitor, detect deviations, generate Eco-Intent

### 7.2 Agent Workflow (Cybernetic Loop)
- **Analysis**: Understand inputs + context
- **Synthesis**: Generate candidate assets (AI proposes)
- **Validation**: Check quality gates (Human approves)
- **Iteration**: Refine until gates pass
- **Key Principle**: Human validates every synthesis output

### 7.3 Agent Constraints
- **LLM-first**: Offload logic to LLM (minimize agent code)
- **Stateless**: Agents don't maintain state between invocations
- **Single Responsibility**: Each agent has one focused task
- **Context-driven**: All decisions based on explicit context

---

## 8. Sub-Vectors (Nested/Concurrent SDLCs)

### 8.1 Definition
- Complex activities spawn their own AI SDLC
- Sub-vectors run concurrently with main SDLC
- Linked through requirement keys

### 8.2 Common Sub-Vectors
- **Architecture as SDLC**: Intent: "Scalable architecture" → Output: ADRs, IaC
- **UAT Test Development as SDLC**: Intent: "UAT coverage" → Output: BDD tests
- **Data Pipeline as SDLC**: Intent: "Analytics data product" → Output: ETL, DQ tests
- **Test Development as SDLC**: Intent: "Test coverage" → Output: Test frameworks
- **Data Science Pipeline as SDLC**: Intent: "ML model" → Output: Feature engineering, training
- **Documentation as SDLC**: Intent: "Complete docs" → Output: API docs, user guides

### 8.3 Synchronization
- Shared requirement keys (natural integration)
- Concurrent execution (single developer, multiple AI agents)
- Dependency management (critical path awareness)

---

## 9. Governance & Quality

### 9.1 Quality Gates (Per Stage)
- **Requirements**: All requirements have unique keys, acceptance criteria
- **Design**: All components mapped to REQ keys, ADRs for strategic decisions
- **Tasks**: All tasks linked to REQ keys, dependencies identified
- **Code**: TDD followed, coverage ≥80%, Key Principles compliance
- **System Test**: Requirement coverage ≥95%, all scenarios pass
- **UAT**: All critical scenarios pass, stakeholder sign-off
- **Runtime**: Telemetry tagged with REQ keys, SLA monitoring

### 9.2 Coverage Requirements
- **Unit Tests**: ≥80% overall, 100% critical paths
- **Integration Tests**: ≥95% requirement coverage
- **BDD Scenarios**: Every REQ must have ≥1 scenario
- **UAT Coverage**: All critical user journeys validated

### 9.3 Continuous Governance
- Not one-time gates, continuous monitoring
- Automated checks in CI/CD pipeline
- Real-time feedback loops
- Governance as code (not manual reviews)

---

## 10. Homeostasis Model Details

### 10.1 Components
- **Target State**: Requirements (REQ-F-*, REQ-NFR-*, REQ-DATA-*)
- **Actual State**: Runtime behavior (metrics, logs, traces)
- **Observer**: Monitors actual state (Datadog, Prometheus, New Relic)
- **Evaluator**: Compares actual vs target (alert rules, SLO checks)
- **Control**: Generate intent when deviation detected

### 10.2 Feedback Types
- **Performance Deviation**: Response time > target → optimization intent
- **Availability Deviation**: Uptime < SLA → reliability intent
- **Data Quality Deviation**: Accuracy < threshold → DQ improvement intent
- **Security Deviation**: Vulnerability detected → remediation intent
- **Cost Deviation**: Budget exceeded → cost optimization intent

### 10.3 Intent Generation
- **Automatic**: Alerts directly create intents (pre-defined rules)
- **Semi-Automatic**: Alerts notify, human creates intent
- **Manual**: Human observes, creates intent
- **Priority**: Remediation > Update > Create

---

## 11. CRUD Work Types

### 11.1 Classification
- **Create**: Build something new (CapEx, greenfield)
- **Update**: Change existing behavior (OpEx, enhancement)
- **Remediation**: Fix risks/bugs (non-discretionary, urgent)
- **Read**: Analysis/discovery (info gathering, investigation)
- **Delete**: Decommission/retire (tech debt reduction, cleanup)

### 11.2 Work Type Characteristics
- **Create**: Full SDLC, extensive testing, architecture review
- **Update**: Regression focus, backward compatibility
- **Remediation**: Fast-track, security review, root cause analysis
- **Read**: Lightweight, documentation output, knowledge transfer
- **Delete**: Deprecation plan, data migration, dependency check

### 11.3 Builder.CRUD
- Single unified pipeline for all work types
- Work type determines control regime (e.g., remediation = higher scrutiny)
- Metadata tracks work type throughout lifecycle

---

## 12. Data Quality Integration

### 12.1 REQ-DATA-* Requirements
- **Completeness**: Mandatory fields, null handling
- **Accuracy**: Validation rules, range checks
- **Consistency**: Cross-field validation, referential integrity
- **Timeliness**: Freshness requirements, latency SLAs
- **Lineage**: Data provenance, transformation tracking
- **Privacy/PII**: Encryption, masking, retention, GDPR compliance

### 12.2 Data Steward Role
- Reviews REQ-DATA-* in Requirements stage
- Validates data models in Design stage
- Signs off UAT data quality
- Monitors runtime data quality metrics

### 12.3 Data Quality Testing
- **System Test**: Automated DQ checks (completeness, accuracy, consistency)
- **UAT**: Business validates data correctness
- **Runtime**: Continuous DQ monitoring (Great Expectations, Deequ)

---

## 13. Deployment Integration

### 13.1 External CI/CD
- AI SDLC hands off to external CI/CD (Jenkins, GitLab CI, GitHub Actions)
- Release manifests list REQ keys
- Deployment is separate concern (not part of SDLC stages)

### 13.2 Release Artifacts
- **Code**: Tagged with version, REQ keys in commit messages
- **Tests**: Test results with REQ coverage matrix
- **Docs**: Updated with new REQ keys
- **Manifests**: YAML/JSON listing deployed REQ keys

### 13.3 Deployment Gates
- All tests pass (unit, integration, BDD)
- Coverage thresholds met
- Security scan clean
- UAT sign-off obtained

---

## 14. Observability & Monitoring

### 14.1 Telemetry Tagging
- **Logs**: Include REQ keys in structured logs
- **Metrics**: Tag metrics with REQ keys (e.g., `req=REQ-F-AUTH-001`)
- **Traces**: Propagate REQ keys through distributed traces
- **Alerts**: Route to Intent Manager with REQ context

### 14.2 Requirement-Level Observability
- Each REQ has dedicated dashboard
- Success rate, latency, error rate per REQ
- SLA compliance per REQ
- Historical trend analysis per REQ

### 14.3 Ecosystem Monitoring
- **Security**: Dependabot, Snyk, GitHub Security Advisories
- **Deprecations**: AWS Trusted Advisor, API changelogs
- **Costs**: CloudWatch billing alerts, cost anomaly detection
- **Performance**: External API latency, third-party SLA monitoring

---

## 15. Category Theory Formalization

### 15.1 𝓒_SDLC Category
- **Objects**: SDLC stages (Requirements, Design, Tasks, Code, Test, UAT, Runtime)
- **Morphisms**: Stage transitions (Requirements → Design)
- **Composition**: Transitive stage flow
- **Identity**: Each stage maps to itself
- **Purpose**: Mathematical model of SDLC structure

### 15.2 Context Comonad
- **Structure**: (Ctx, ε, δ)
- **ε (extract)**: Current context
- **δ (duplicate)**: Context nesting (inheritance)
- **Purpose**: Formalize context propagation and composition

### 15.3 Traceability Fibration
- **Structure**: p: 𝓔_Assets → 𝓑_Req
- **𝓔_Assets**: Total space (all assets: code, tests, docs)
- **𝓑_Req**: Base space (all requirements)
- **p (projection)**: Maps assets to their requirements
- **Purpose**: Formalize requirement traceability

### 15.4 Ecosystem as Ambient Category
- **Concept**: E(t) is the environment we operate within (not construct)
- **Properties**: External, evolving, constraining
- **Relationship**: 𝓒_SDLC operates inside 𝓔_Ecosystem(t)
- **Purpose**: Distinguish between what we build vs what we use

---

## 16. Personas & Collaboration

### 16.1 Human Personas
- **Product Owner**: Intent prioritization, acceptance criteria
- **Business Analyst**: Requirements elicitation, BDD scenarios
- **Tech Lead/Architect**: Design decisions, ADRs, ecosystem choices
- **Developer**: Code implementation, unit tests, TDD
- **Data Engineer**: Data pipelines, data quality, lineage
- **QA Engineer**: System test, BDD automation, requirement validation
- **Business SME**: UAT validation, sign-off
- **Data Steward**: Data quality review, privacy compliance
- **DevOps/SRE**: Runtime monitoring, alerts, Eco-Intent generation

### 16.2 AI Agent Personas
- One agent per stage (7 total)
- Agents propose, humans decide
- Agents follow explicit context
- Agents validate against quality gates

### 16.3 Collaboration Patterns
- **Pair Programming with AI**: Human + Code Agent, TDD workflow
- **Concurrent Development**: Single human + multiple AI agents (sub-vectors)
- **Review Cycles**: AI proposes, human reviews, iterate until approved

---

## 17. Future-Ready Concepts

### 17.1 AI-Generated Applications
- Requirements provide deterministic control over AI behavior
- Automatic observer/evaluator generation from requirements
- Runtime assurance for AI-generated code
- Post-run verification of probabilistic LLM outputs

### 17.2 On-Demand Application Building
- Intent → Requirements → Auto-generate application
- Traceability ensures correctness
- Homeostasis model validates runtime behavior
- Rebuild from requirements when needed

### 17.3 Adaptive Requirements
- Requirements evolve based on runtime feedback
- Machine learning on deviation patterns
- Predictive intent generation
- Self-optimizing systems

---

## 18. Implementation Patterns

### 18.1 Requirement Key Propagation
- **Code comments**: `# Implements: REQ-F-AUTH-001`
- **Test names**: `test_user_login_REQ_F_AUTH_001()`
- **Commit messages**: `Add login (REQ-F-AUTH-001)`
- **Log statements**: `logger.info("Login failed", extra={"req": "REQ-F-AUTH-001"})`
- **Metrics**: `auth_success_rate{req="REQ-F-AUTH-001"}`

### 18.2 BDD Scenario Format
```gherkin
Feature: [Capability]
  # Validates: REQ-F-AUTH-001

  Scenario: [Test case]
    Given [precondition]
    When [action]
    Then [expected result]
```

### 18.3 ADR Template
```markdown
# ADR-XXX: [Decision]

## Context
Requirements: REQ-*
Ecosystem constraints: team, timeline, budget, compliance

## Decision
Selected: [Option] | Rejected: [Alternatives]

## Ecosystem Constraints Acknowledged
- Team knows X, doesn't know Y
- Timeline Z months
- Budget $W/month

## Constraints Imposed Downstream
- Code stage must use library L
- Runtime must deploy to platform P
```

---

## 19. Versioning & Evolution

### 19.1 Requirement Versioning
- Requirements can evolve (not immutable content, immutable keys)
- Version tracked in requirement metadata
- Traceability preserved across versions
- Backward compatibility considerations

### 19.2 Context Versioning
- Git-tracked context configurations
- Tagged releases (v1.0, v2.0)
- Merge strategies for federated contexts
- Override precedence rules

### 19.3 Methodology Versioning
- Current version: 1.2
- Semantic versioning (major.minor)
- Changelog documents evolution
- Migration guides for major versions

---

## 20. Plugin & Marketplace

### 20.1 Claude Code Plugins
- Installable methodology as plugin
- Claude automatically follows 7-stage SDLC
- Context loaded from plugin
- Plugin structure: `.claude-plugin/plugin.json`

### 20.2 Federated Marketplace
- **Corporate Marketplace**: Organization-wide standards
- **Division Marketplace**: Division-specific extensions
- **Team Marketplace**: Team customizations
- **Project Plugin**: Project-specific context
- **Loading Order**: Corporate → Division → Team → Project (later overrides earlier)

### 20.3 Plugin Types
- **Methodology**: aisdlc-methodology (7-stage SDLC)
- **Language Standards**: python-standards, javascript-standards
- **Domain Standards**: payment-services, healthcare-compliance
- **Project Context**: customer-portal, api-gateway

---

## Concept Audit Checklist

When updating methodology, verify:

- [ ] All 7 stages documented
- [ ] All 4 REQ types defined (F, NFR, DATA, BR)
- [ ] TDD workflow (RED→GREEN→REFACTOR→COMMIT) present
- [ ] BDD structure (Given/When/Then) present
- [ ] All 7 Key Principles listed
- [ ] Homeostasis model explained (Observer, Evaluator, Intent)
- [ ] E(t) ecosystem concepts present
- [ ] ADRs documented
- [ ] Eco-Intent flow described
- [ ] Traceability (Golden Thread) explained
- [ ] All personas defined (9 human + 7 AI)
- [ ] Quality gates per stage listed
- [ ] Coverage requirements specified
- [ ] CRUD work types explained
- [ ] Sub-vectors concept present
- [ ] Category theory (optional) referenced
- [ ] Context framework documented
- [ ] Plugin system described

---

**Version**: 1.2
**Last Updated**: 2025-11-20
**Maintained By**: AI SDLC methodology team
**Purpose**: Living document - update as methodology evolves

**Excellence or nothing** 🔥
