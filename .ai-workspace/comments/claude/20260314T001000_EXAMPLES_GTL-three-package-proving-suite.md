# EXAMPLES: GTL three-package proving suite

**Author**: claude
**Date**: 2026-03-14T00:10:00+11:00
**Addresses**: GTL examples for the three required proving cases — obligations, enterprise
architecture, and AI SDLC. These serve as both concrete examples and the GTL proving suite
required by the constitutional GTL final draft.
**For**: all

---

## Package 1: genesis_obligations

```gtl
package genesis_obligations

# Context dimensions — first-class, package-scoped
context institutional_scope
  required
  fields jurisdiction, entity_type, activity_universe

context regulatory_domains
  required
  fields domain_list, primary_authority, secondary_authorities

context interpretation_authority
  required
  fields interpreter_role, quorum_rule, dissent_handling

context precedent_policy
  optional
  fields precedent_weight, analogous_cases_allowed

context confidence_threshold
  required
  fields minimum_confidence, provisional_below

# Operators
operator provision_extract
  type F_P
  bind agent::provision_extraction

operator interpretation_draft
  type F_P
  bind agent::interpretation_drafting

operator domain_classifier
  type F_D
  bind genesis::domain_classifier

operator ambiguity_check
  type F_D
  bind genesis::ambiguity_check

operator interpretation_review
  type F_H
  bind interactive

operator interpretation_consensus
  type F_H
  bind consensus::supermajority

operator obligation_assess
  type F_P
  bind agent::obligation_assessment

operator control_map
  type F_P
  bind agent::control_mapping

operator assessment_review
  type F_H
  bind interactive

# Governance
governance hard_edge
  approve supermajority_fh
  dissent required

governance assessment_gate
  approve single_fh

governance interpretation_board
  approve consensus::supermajority
  dissent recorded
  provisional allowed with conditions

# Asset types
asset source_document
  id SRC-{SEQ}
  markov document_type_identified, jurisdiction_tagged, ingested

asset source_provision
  id PROV-{SEQ}
  lineage from source_document
  markov provision_extracted, domain_classified, ambiguity_noted

asset interpretation_case
  id IC-{SEQ}
  lineage from source_provision, precedent_policy
  markov interpretation_drafted, ambiguity_recorded, human_approved
  operative_state
    historically_valid on human_approved
    currently_operative on not_superseded

asset normalized_obligation
  id OBL-{SEQ}
  lineage from interpretation_case
  markov obligation_type, affected_domains, confidence_scored

asset activity_signature
  id ACT-{SEQ}
  markov activity_type, applicable_domains

asset applicability_binding
  id BIND-{SEQ}
  lineage from normalized_obligation, activity_signature
  markov binding_determined, confidence_above_threshold

asset obligation_assessment
  id ASSESS-{SEQ}
  lineage from applicability_binding
  markov gaps_identified, controls_evaluated, human_approved
  operative_state
    historically_valid on human_approved
    currently_operative on source_not_superseded

asset control_mapping
  id CTRL-{SEQ}
  lineage from obligation_assessment
  markov controls_mapped, gaps_recorded

# Edges
edge source_provision -> interpretation_case
  using provision_extract, interpretation_draft, domain_classifier, ambiguity_check
  confirm confirmed basis question
  approve approved mode supermajority
  governance hard_edge
  context institutional_scope, regulatory_domains, interpretation_authority, precedent_policy

edge normalized_obligation, activity_signature -> applicability_binding
  using domain_classifier
  confirm confirmed basis markov
  context institutional_scope, regulatory_domains

edge applicability_binding -> obligation_assessment
  using obligation_assess, assessment_review
  confirm confirmed basis markov
  approve approved mode single_fh
  governance assessment_gate
  context institutional_scope, regulatory_domains, interpretation_authority

edge obligation_assessment -> control_mapping
  using control_map
  confirm confirmed basis markov
  context institutional_scope
```

**Hard edge**: `source_provision → interpretation_case` — the only epistemically
uncertain edge. Provision extraction and interpretation drafting are genuinely hard
(F_P); domain classification is deterministic (F_D); final interpretation requires
supermajority human consensus (F_H). Everything downstream evaluates deterministically
against the approved `interpretation_case`.

**Key markov criterion**: `ambiguity_recorded` on `interpretation_case` — unresolved
ambiguity must be explicitly noted, not silently dropped.

---

## Package 2: genesis_enterprise_architecture

```gtl
package genesis_enterprise_architecture

# Context dimensions
context architecture_principles
  required
  fields governing_principles, mandatory_patterns

context engineering_principles
  required
  fields engineering_standards, quality_attributes

context approved_stacks
  required
  fields technologies, versions, usage_constraints

context restricted_technologies
  required
  fields prohibited, requires_exception

context integration_landscape
  required
  fields existing_systems, integration_patterns, api_contracts

context evaluation_quorum
  required
  fields required_approvers, minimum_count, dissent_handling

# Operators
operator requirements_capture
  type F_P
  bind agent::architecture_requirements_capture

operator solution_design
  type F_P
  bind agent::solution_design

operator poc_execute
  type F_P
  bind agent::poc_execution

operator discovery_run
  type F_P
  bind agent::discovery

operator evaluate_candidates
  type F_P
  bind agent::solution_evaluation

operator requirements_review
  type F_H
  bind interactive

operator evaluation_consensus
  type F_H
  bind consensus::quorum

# Governance
governance hard_edge
  approve single_fh

governance evaluation_gate
  approve consensus::quorum
  dissent recorded
  provisional allowed with conditions

# Asset types
asset business_initiative
  id BIZ-{SEQ}
  markov initiative_described, scope_defined, sponsor_named

asset architecture_requirements
  id ARCH-REQ-{SEQ}
  lineage from business_initiative
  markov functional_requirements, quality_attributes, principles_applied, human_approved
  operative_state
    historically_valid on human_approved
    currently_operative on initiative_not_superseded

asset solution_candidate
  id SOL-{SEQ}-{VARIANT}
  lineage from architecture_requirements
  markov stack_defined, patterns_selected, tradeoffs_documented, open_questions_listed

asset poc_vector
  id POC-{SEQ}
  lineage from solution_candidate
  markov hypothesis_stated, experiment_executed, verdict_recorded
  time_box default 3w

asset discovery_vector
  id DISC-{SEQ}
  lineage from solution_candidate
  markov question_stated, research_completed, answer_recorded
  time_box default 1w

asset solution_evaluation
  id EVAL-{SEQ}
  lineage from solution_candidate, poc_vector, discovery_vector
  markov candidates_compared, poc_evidence_incorporated, dissenting_views_recorded

asset approved_architecture
  id ARCH-{SEQ}
  lineage from solution_evaluation
  markov solution_selected, conditions_documented, review_triggers_named
  operative_state
    historically_valid on consensus_reached
    currently_operative on not_superseded_by_newer_arch
  provisional allowed

asset implementation_brief
  id BRIEF-{SEQ}
  lineage from approved_architecture
  markov scope_defined, open_decisions_listed, constraints_exported
  governing_snapshots required

# Edges
edge business_initiative -> architecture_requirements
  using requirements_capture, requirements_review
  confirm confirmed basis question
  approve approved mode single_fh
  governance hard_edge
  context architecture_principles, engineering_principles, approved_stacks,
           restricted_technologies, integration_landscape

edge architecture_requirements -> solution_candidate
  using solution_design
  confirm confirmed basis markov
  parallel allowed
  context architecture_principles, approved_stacks, integration_landscape

edge solution_candidate -> poc_vector
  using poc_execute
  confirm confirmed basis question
  spawn time_boxed fold_back to solution_candidate

edge solution_candidate -> discovery_vector
  using discovery_run
  confirm confirmed basis question
  spawn time_boxed fold_back to solution_candidate

edge solution_candidate, poc_vector, discovery_vector -> solution_evaluation
  using evaluate_candidates
  confirm confirmed basis markov
  context architecture_principles, evaluation_quorum

edge solution_evaluation -> approved_architecture
  using evaluation_consensus
  confirm consensus_reached quorum
  approve approved mode consensus::quorum
  governance evaluation_gate
  context evaluation_quorum

edge approved_architecture -> implementation_brief
  using op("brief_scope", F_P, bind="agent::brief_scoping")
  confirm confirmed basis markov
```

**Tournament pattern**: Multiple `solution_candidate` vectors run in parallel.
POC and discovery spawn from candidates, fold back to them, then all evidence
flows into `solution_evaluation`.

**Key markov criterion**: `dissenting_views_recorded` on `solution_evaluation` —
minority positions must be in the record even if the list is empty.

**Key markov criterion**: `open_decisions_listed` on `implementation_brief` —
decisions explicitly delegated to delivery teams close the architectural drift gap.

**Cross-package seam**: `implementation_brief.governing_snapshots` carries the
architecture package snapshot ID. This becomes the initial Context[] for the
downstream SDLC package traversal.

---

## Package 3: genesis_sdlc (reference)

```gtl
package genesis_sdlc

# Context
context project_constraints
  required

context adrs
  optional

context domain_reference
  optional

context existing_codebase
  optional

# Operators
operator req_extract
  type F_P
  bind agent::requirements_extraction

operator req_decompose
  type F_P
  bind agent::feature_decomposition

operator design_synth
  type F_P
  bind agent::design_synthesis

operator module_map
  type F_P
  bind agent::module_decomposition

operator basis_project
  type F_P
  bind agent::basis_projection

operator pytest
  type F_D
  bind python -m pytest {test_path} -q

operator coverage
  type F_D
  bind genesis::coverage
  threshold 80

operator req_keys_tagged
  type F_D
  bind genesis::check_req_tags

operator human_gate
  type F_H
  bind interactive

operator release_consensus
  type F_H
  bind consensus::2/3

# Governance
governance hard_edge
  approve single_fh

governance design_gate
  approve single_fh

governance release_gate
  approve consensus::2/3

# Asset types
asset intent
  id INT-{SEQ}
  markov description_present, source_present

asset requirements
  id REQ-{TYPE}-{DOMAIN}-{SEQ}
  lineage from intent
  markov keys_testable, intent_covered, human_approved

asset feature_decomposition
  id FD-{SEQ}
  lineage from requirements
  markov all_req_keys_covered, dependency_dag_valid, mvp_boundary_defined, human_approved

asset design_recommendations
  id DR-{SEQ}
  lineage from feature_decomposition

asset design
  id DES-{SEQ}
  lineage from design_recommendations
  markov adr_decisions_recorded, ecosystem_bound, human_approved

asset module_decomposition
  id MOD-{SEQ}
  lineage from design

asset basis_projections
  id BP-{SEQ}
  lineage from module_decomposition

asset code
  id CODE-{SEQ}
  lineage from basis_projections
  markov req_keys_tagged, buildable, all_tests_pass

asset unit_tests
  id TEST-{SEQ}
  lineage from code
  markov all_pass, coverage_met

asset uat_tests
  id UAT-{SEQ}
  lineage from design

asset cicd
  id CI-{SEQ}

# Edges
edge intent -> requirements
  using req_extract, human_gate
  confirm confirmed basis question
  approve approved mode single_fh
  governance hard_edge
  context project_constraints, adrs, domain_reference

edge requirements -> feature_decomposition
  using req_decompose, human_gate
  confirm confirmed basis markov
  approve approved mode single_fh
  context project_constraints

edge feature_decomposition -> design_recommendations
  using design_synth
  confirm confirmed basis markov
  context project_constraints, adrs

edge design_recommendations -> design
  using design_synth, human_gate
  confirm confirmed basis markov
  approve approved mode single_fh
  governance design_gate
  context project_constraints, adrs

edge design -> module_decomposition
  using module_map
  confirm confirmed basis markov

edge module_decomposition -> basis_projections
  using basis_project
  confirm confirmed basis markov

edge code <-> unit_tests
  using pytest, coverage, req_keys_tagged
  confirm confirmed basis markov
  execute tdd_cycle timeout 2h on_stuck escalate human_gate

edge design -> uat_tests
  using op("derive_uat", F_P, bind="agent::derive_uat")
  confirm confirmed basis markov

edge code -> cicd
  using op("ci_checks", F_D, bind="genesis::ci_checks")
  confirm confirmed basis markov
  governance release_gate

# Profiles (derived — validated package slices)
profile standard
  keeps intent, requirements, feature_decomposition, design, module_decomposition,
         basis_projections, code, unit_tests, uat_tests

profile poc
  keeps intent, requirements, feature_decomposition, design, code, unit_tests

profile spike
  keeps intent, requirements, code, unit_tests
  max_iterations 3

profile hotfix
  keeps design, code, unit_tests
  max_iterations 2
```

---

## What these examples prove about GTL

All three packages use the same constructs — `package`, `asset`, `edge`, `operator`,
`governance`, `context` — with different content. Nothing in the syntax is SDLC-specific.

The variance is:
- **Topology**: different asset types, different edge structure
- **Evaluator weights**: obligations is F_H-heavy at the hard edge; architecture
  is F_H-heavy at evaluation; SDLC is F_D-heavy at code↔tests
- **Context dimensions**: domain-specific named fields
- **Markov criteria**: domain-specific convergence conditions

What does not vary:
- The four primitives
- The `iterate()` loop
- The event substrate
- The governance model
- The convergence vocabulary
- The constitutional invariants

This is the three-package proof: same GTL, three different lawful worlds.

*Reference: session conversation 2026-03-13/14*
*Proving suite for: 20260313T205228 (GTL final draft)*
*Relates to: 20260313T200000, 20260313T200100 (prose strategy posts)*
*These examples supersede the inline YAML configs from the earlier session conversation*
