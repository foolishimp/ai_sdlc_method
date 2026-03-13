# EXAMPLES: genesis_obligations in four dialects — comparison

**Author**: claude
**Date**: 2026-03-14T00:20:00+11:00
**Addresses**: same package expressed in each syntax dialect considered during the
GTL design conversation — for comparison and design evaluation
**For**: all

The obligations package hard edge (`source_provision → interpretation_case`) is used
as the comparison case — it is the most structurally demanding edge, requiring F_P,
F_D, and F_H in sequence with supermajority consensus and mandatory dissent recording.

---

## Dialect 1: Current YAML (graph_topology.yml style)

What Genesis uses today. Static config. No constitutional payload.

```yaml
# graph_topology.yml — genesis_obligations (YAML dialect)
nodes:
  - name: source_document
    id: source_document
  - name: source_provision
    id: source_provision
  - name: interpretation_case
    id: interpretation_case
  - name: normalized_obligation
    id: normalized_obligation
  - name: obligation_assessment
    id: obligation_assessment
  - name: control_mapping
    id: control_mapping

edges:
  - source: source_document
    target: source_provision
  - source: source_provision
    target: interpretation_case
  - source: interpretation_case
    target: normalized_obligation
  - source: normalized_obligation
    target: obligation_assessment
  - source: obligation_assessment
    target: control_mapping
```

**What's missing**: identity formats, markov criteria, lineage, governance rules,
evaluator types, context dimensions, convergence vocabulary, snapshot binding,
operative state, constitutional invariants. Everything constitutional is absent.
The edges are bare topology — nothing about how or when they converge.

---

## Dialect 2: ADR-S-035 Python DSL (OO builder style)

ADR-S-035's proposed direction. Better than YAML for authoring, but semantically
wrong — Python is the semantics, not a carrier.

```python
# genesis_obligations.py — ADR-S-035 Python DSL dialect

from genesis.gtl import Package, Asset, Edge, Operator, Governance, Context

# Operators
provision_extract    = Operator("provision_extract",    type=F_P, bind="agent::provision_extraction")
interpretation_draft = Operator("interpretation_draft", type=F_P, bind="agent::interpretation_drafting")
domain_classifier    = Operator("domain_classifier",    type=F_D, bind="genesis::domain_classifier")
ambiguity_check      = Operator("ambiguity_check",      type=F_D, bind="genesis::ambiguity_check")
interpretation_consensus = Operator("interpretation_consensus", type=F_H, bind="consensus::supermajority")

# Assets
source_provision    = Asset("source_provision",    id_format="PROV-{SEQ}")
interpretation_case = Asset("interpretation_case", id_format="IC-{SEQ}",
                            markov=["interpretation_drafted", "ambiguity_recorded", "human_approved"],
                            lineage=["source_provision", "precedent_policy"])

# Governance
hard_edge = Governance("hard_edge", approve="supermajority_fh", dissent_required=True)

# Package
obligations = Package("genesis_obligations") \
    .context(Context("institutional_scope", required=True)) \
    .context(Context("regulatory_domains", required=True)) \
    .context(Context("interpretation_authority", required=True)) \
    .assets(source_provision, interpretation_case) \
    .edges(
        Edge(source_provision, interpretation_case)
            .using(provision_extract, interpretation_draft, domain_classifier, ambiguity_check)
            .confirm("question_answered")
            .approve(hard_edge)
            .context("institutional_scope", "regulatory_domains", "interpretation_authority")
    ) \
    .governance(hard_edge)
```

**Problems**: Arbitrary Python is allowed anywhere. The `.using()` call could
contain imperative logic. Type safety is weak — no compiler rejection of bad
structure. The OO builder style is verbose and requires knowing Python. Reading
it as a constitutional declaration requires mentally stripping the Python out.

---

## Dialect 3: Python algebraic/Scala-style (Codex sketch direction)

Codex's intermediate direction — Python as carrier, Scala-ish algebra as semantics.

```python
# genesis_obligations.py — Python algebraic dialect

from genesis.gtl import *

# Operators
provision_extract    = op("provision_extract",    F_P, bind="agent::provision_extraction")
interpretation_draft = op("interpretation_draft", F_P, bind="agent::interpretation_drafting")
domain_classifier    = op("domain_classifier",    F_D, bind="genesis::domain_classifier")
ambiguity_check      = op("ambiguity_check",      F_D, bind="genesis::ambiguity_check")
interpretation_board = op("interpretation_board", F_H, bind="consensus::supermajority")

# Asset declarations
source_provision    = asset("source_provision").id("PROV-{SEQ}")
interpretation_case = asset("interpretation_case").id("IC-{SEQ}") \
    .lineage(from_=["source_provision"]) \
    .markov("interpretation_drafted", "ambiguity_recorded", "human_approved") \
    .operative(historically_valid="human_approved", currently_operative="not_superseded")

# Governance
hard_edge = governance("hard_edge").approve(supermajority_fh()).dissent(required=True)

# Package
obligations = (
    package("genesis_obligations")
    .context(
        context("institutional_scope").required(),
        context("regulatory_domains").required(),
        context("interpretation_authority").required(),
        context("precedent_policy").optional(),
    )
    .assets(source_provision, interpretation_case)
    .edges(
        source_provision >> interpretation_case @ (
            provision_extract + interpretation_draft + domain_classifier + ambiguity_check,
            confirm(question_answered()),
            approve(hard_edge),
        )
    )
)
```

**Better**: The `@` operator and `+` for operator composition are more algebraic.
Still Python — arbitrary Python could still creep in via `.context()` callbacks or
custom `__rshift__` implementations. Validation is in runtime errors, not in a
compiler. Harder to diff cleanly. The `>>` and `@` operators are creative but
require knowing the convention.

---

## Dialect 4: Declarative GTL (target syntax)

The canonical target — AI-authored, human-audited, compiler-validated.

```gtl
# genesis_obligations — declarative GTL dialect

package genesis_obligations

context institutional_scope
  required
  fields jurisdiction, entity_type, activity_universe

context regulatory_domains
  required
  fields domain_list, primary_authority

context interpretation_authority
  required
  fields interpreter_role, quorum_rule, dissent_handling

context precedent_policy
  optional

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

operator interpretation_board
  type F_H
  bind consensus::supermajority

governance hard_edge
  approve supermajority_fh
  dissent required

asset source_provision
  id PROV-{SEQ}
  markov provision_extracted, domain_classified, ambiguity_noted

asset interpretation_case
  id IC-{SEQ}
  lineage from source_provision
  markov interpretation_drafted, ambiguity_recorded, human_approved
  operative
    historically_valid on human_approved
    currently_operative on not_superseded

edge source_provision -> interpretation_case
  using provision_extract, interpretation_draft, domain_classifier, ambiguity_check
  confirm confirmed basis question
  approve approved mode supermajority_fh
  governance hard_edge
  context institutional_scope, regulatory_domains, interpretation_authority, precedent_policy
```

**What this has that the others don't**:
- No arbitrary Python anywhere — the surface is fully controlled
- `operative` block on `asset` — `historically_valid` vs `currently_operative` first-class
- `dissent required` on governance — structural, not a comment
- `confirm confirmed basis question` — explicit convergence vocabulary
- `context` on edge — which dimensions are loaded for this traversal
- Diffable — one declaration per line, no nested Python expressions
- Compiler can reject: missing required context, unknown operator type, invalid
  convergence vocabulary, malformed id format, circular lineage

**What it still needs for the compiler**:
- BNF grammar to drive parsing and rejection
- Normalized IR that all four dialects could theoretically compile to
- The `operative` block semantics formally specified

---

## Comparison table

| Property | YAML | Python OO | Python algebraic | Declarative GTL |
|----------|------|-----------|-----------------|-----------------|
| Constitutional payload | ✗ | Partial | Partial | ✓ |
| AI-generatable | ✓ | ✓ | ✓ | ✓ |
| Compiler-rejectable | ✗ | Partial | Partial | ✓ |
| Human-auditable | Poor | Poor | Medium | Good |
| Diff-friendly | ✓ | ✗ | Medium | ✓ |
| `historically_valid` | ✗ | Manual | Manual | ✓ |
| `dissent required` | ✗ | Via flag | Via param | ✓ |
| No arbitrary logic | ✓ | ✗ | ✗ | ✓ |
| Standalone syntax | ✓ | ✗ | ✗ | ✓ |
| Mermaid renderable | ✓ | ✓ | ✓ | ✓ |

The declarative GTL wins on the dimensions that matter for the constitutional OS:
compiler enforcement, diffability, and full constitutional payload. It loses
nothing except the ability to embed arbitrary Python — which is a feature, not a bug.

*Reference: session conversation 2026-03-13/14*
*Relates to: 20260314T001000_EXAMPLES_GTL-three-package-proving-suite.md*
*ADR-S-035 Python OO style shown as Dialect 2 — this is what the revision supersedes*
