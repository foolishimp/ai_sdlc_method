"""
genesis_obligations — GTL as plain Python objects

The hard edge pattern: F_P extraction → F_D checks → F_H supermajority board.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2]))

from gtl.core import (
    Package, Asset, Edge, Operator, Rule, Context, Overlay,
    F_D, F_P, F_H, consensus,
    OPERATIVE_ON_APPROVED, OPERATIVE_ON_APPROVED_NOT_SUPERSEDED,
)

# ── Rules ──────────────────────────────────────────────────────────────────

hard_edge = Rule(
    name="hard_edge",
    approve=consensus(3, 4),
    dissent="required",
    provisional=True,
)

standard_gate = Rule(
    name="standard_gate",
    approve=consensus(1, 1),
    dissent="recorded",
)

# ── Operators ──────────────────────────────────────────────────────────────

provision_extract = Operator("provision_extract", F_P, "agent://provision_extraction")
interpret_draft   = Operator("interpret_draft",   F_P, "agent://interpretation_drafting")
domain_classify   = Operator("domain_classify",   F_D, "check://domain_classifier")
ambiguity_check   = Operator("ambiguity_check",   F_D, "check://ambiguity_recorded")
obligation_assess = Operator("obligation_assess", F_P, "agent://obligation_assessment")
control_map_op    = Operator("control_map",       F_P, "agent://control_mapping")
human_gate        = Operator("human_gate",        F_H, "fh://single")
interp_board      = Operator("interp_board",      F_H, "fh://consensus/3-4")

# ── Context ────────────────────────────────────────────────────────────────

institutional_scope = Context(
    name="institutional_scope",
    locator="git://github.com/org/obligations.git//ctx/institutional.yml@abc123",
    digest="sha256:9c1d3fabc...",
)

interpretation_authority = Context(
    name="interpretation_authority",
    locator="git://github.com/org/obligations.git//ctx/authority.yml@def456",
    digest="sha256:4a7b2edef...",
)

regulatory_domains = Context(
    name="regulatory_domains",
    locator="git://github.com/org/obligations.git//ctx/regulatory.yml@ghi789",
    digest="sha256:8f2c5aghi...",
)

# ── Assets ─────────────────────────────────────────────────────────────────

source_provision = Asset(
    name="source_provision",
    id_format="PROV-{SEQ}",
    markov=["extracted", "domain_classified", "ambiguity_noted"],
)

interpretation_case = Asset(
    name="interpretation_case",
    id_format="IC-{SEQ}",
    lineage=[source_provision],
    markov=["interpretation_drafted", "ambiguity_recorded"],
    operative=OPERATIVE_ON_APPROVED_NOT_SUPERSEDED,
)

normalized_obligation = Asset(
    name="normalized_obligation",
    id_format="OBL-{SEQ}",
    lineage=[interpretation_case],
    markov=["taxonomy_complete", "scope_bound"],
)

activity_signature = Asset(
    name="activity_signature",
    id_format="ACT-{SEQ}",
    markov=["scope_bound"],
)

applicability_binding = Asset(
    name="applicability_binding",
    id_format="APPL-{SEQ}",
    lineage=[normalized_obligation, activity_signature],
    markov=["applicability_explained"],
)

# ── Edges ──────────────────────────────────────────────────────────────────

interpret = Edge(
    name="interpret",
    source=source_provision,
    target=interpretation_case,
    using=[provision_extract, interpret_draft, domain_classify, ambiguity_check],
    confirm="question",
    rule=hard_edge,
    context=[institutional_scope, interpretation_authority, regulatory_domains],
)

normalize = Edge(
    name="normalize",
    source=interpretation_case,
    target=normalized_obligation,
    using=[interpret_draft],
    confirm="markov",
    context=[institutional_scope],
)

apply = Edge(
    name="apply",
    source=[normalized_obligation, activity_signature],   # product arrow: A × B -> C
    target=applicability_binding,
    using=[domain_classify],
    confirm="markov",
    context=[institutional_scope, regulatory_domains],
)

# ── Package ────────────────────────────────────────────────────────────────

genesis_obligations = Package(
    name="genesis_obligations",
    assets=[
        source_provision,
        interpretation_case,
        normalized_obligation,
        activity_signature,
        applicability_binding,
    ],
    edges=[interpret, normalize, apply],
    operators=[
        provision_extract, interpret_draft, domain_classify,
        ambiguity_check, obligation_assess, control_map_op,
        human_gate, interp_board,
    ],
    rules=[hard_edge, standard_gate],
    contexts=[institutional_scope, interpretation_authority, regulatory_domains],
)

if __name__ == "__main__":
    print(genesis_obligations.describe())
