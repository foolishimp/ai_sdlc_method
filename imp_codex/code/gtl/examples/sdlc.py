"""
genesis_sdlc — GTL as plain Python objects

The default software delivery package. TDD co-evolution, profiles as restriction overlays.
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

hard_edge    = Rule("hard_edge",    approve=consensus(1, 1), dissent="recorded")
design_gate  = Rule("design_gate",  approve=consensus(1, 1), dissent="recorded")
release_gate = Rule("release_gate", approve=consensus(2, 3), dissent="required")

# ── Operators ──────────────────────────────────────────────────────────────

req_extract    = Operator("req_extract",    F_P, "agent://requirements_extraction")
req_decompose  = Operator("req_decompose",  F_P, "agent://feature_decomposition")
design_synth   = Operator("design_synth",   F_P, "agent://design_synthesis")
module_map     = Operator("module_map",     F_P, "agent://module_decomposition")
basis_project  = Operator("basis_project",  F_P, "agent://basis_projection")
pytest_op      = Operator("pytest",         F_D, "exec://python -m pytest {path} -q")
coverage_check = Operator("coverage_check", F_D, "metric://coverage >= 80")
req_tags       = Operator("req_tags",       F_D, "check://req_tags_present")
human_gate     = Operator("human_gate",     F_H, "fh://single")
release_board  = Operator("release_board",  F_H, "fh://consensus/2-3")

# ── Context ────────────────────────────────────────────────────────────────

project_constraints = Context(
    name="project_constraints",
    locator="git://github.com/org/project.git//constraints/project.yml@abc123",
    digest="sha256:1a2b3cabc...",
)

adrs = Context(
    name="adrs",
    locator="git://github.com/org/project.git//adrs/index.yml@def456",
    digest="sha256:4d5e6fdef...",
)

# ── Assets ─────────────────────────────────────────────────────────────────

intent = Asset(
    name="intent",
    id_format="INT-{SEQ}",
    markov=["description_present", "source_present"],
)

requirements = Asset(
    name="requirements",
    id_format="REQ-{TYPE}-{DOMAIN}-{SEQ}",
    lineage=[intent],
    markov=["keys_testable", "intent_covered"],
    operative=OPERATIVE_ON_APPROVED,
)

feature_decomposition = Asset(
    name="feature_decomposition",
    id_format="FD-{SEQ}",
    lineage=[requirements],
    markov=["all_req_keys_covered", "dependency_dag_valid", "mvp_boundary_defined"],
    operative=OPERATIVE_ON_APPROVED,
)

design = Asset(
    name="design",
    id_format="DES-{SEQ}",
    lineage=[feature_decomposition],
    markov=["adrs_recorded", "ecosystem_bound"],
    operative=OPERATIVE_ON_APPROVED_NOT_SUPERSEDED,
)

module_decomposition = Asset(
    name="module_decomposition",
    id_format="MOD-{SEQ}",
    lineage=[design],
)

basis_projections = Asset(
    name="basis_projections",
    id_format="BP-{SEQ}",
    lineage=[module_decomposition],
)

code = Asset(
    name="code",
    id_format="CODE-{SEQ}",
    lineage=[basis_projections],
    markov=["req_tags_present", "buildable"],
)

unit_tests = Asset(
    name="unit_tests",
    id_format="TEST-{SEQ}",
    lineage=[code],
    markov=["all_pass", "coverage_met"],
)

uat_tests = Asset(
    name="uat_tests",
    id_format="UAT-{SEQ}",
    lineage=[design],
    markov=["scenarios_covered"],
    operative=OPERATIVE_ON_APPROVED,
)

# ── Edges ──────────────────────────────────────────────────────────────────

interpret = Edge(
    name="interpret",
    source=intent,
    target=requirements,
    using=[req_extract, human_gate],
    confirm="question",
    rule=hard_edge,
    context=[project_constraints, adrs],
)

decompose = Edge(
    name="decompose",
    source=requirements,
    target=feature_decomposition,
    using=[req_decompose, human_gate],
    confirm="markov",
    rule=hard_edge,
    context=[project_constraints],
)

design_from_features = Edge(
    name="design_from_features",
    source=feature_decomposition,
    target=design,
    using=[design_synth, human_gate],
    confirm="markov",
    rule=design_gate,
    context=[project_constraints, adrs],
)

decompose_modules = Edge(
    name="decompose_modules",
    source=design,
    target=module_decomposition,
    using=[module_map],
    confirm="markov",
    context=[project_constraints, adrs],
)

project_basis = Edge(
    name="project_basis",
    source=module_decomposition,
    target=basis_projections,
    using=[basis_project],
    confirm="markov",
    context=[project_constraints],
)

tdd = Edge(
    name="tdd",
    source=[code, unit_tests],          # co-evolution: both assets mutate together
    target=unit_tests,
    co_evolve=True,
    using=[pytest_op, coverage_check, req_tags],
    confirm="markov",
    context=[project_constraints],
)

derive_uat = Edge(
    name="derive_uat",
    source=design,
    target=uat_tests,
    using=[req_decompose],
    confirm="markov",
    context=[project_constraints],
)

release = Edge(
    name="release",
    source=code,
    target=code,
    using=[release_board],
    confirm="markov",
    rule=release_gate,
)

# ── Package ────────────────────────────────────────────────────────────────

genesis_sdlc = Package(
    name="genesis_sdlc",
    assets=[
        intent, requirements, feature_decomposition, design,
        module_decomposition, basis_projections, code, unit_tests, uat_tests,
    ],
    edges=[
        interpret, decompose, design_from_features, decompose_modules,
        project_basis, tdd, derive_uat, release,
    ],
    operators=[
        req_extract, req_decompose, design_synth, module_map, basis_project,
        pytest_op, coverage_check, req_tags, human_gate, release_board,
    ],
    rules=[hard_edge, design_gate, release_gate],
    contexts=[project_constraints, adrs],
)

# ── Profiles (restriction overlays) ───────────────────────────────────────

standard = Overlay(
    name="standard",
    on=genesis_sdlc,
    restrict_to=[
        "intent", "requirements", "feature_decomposition", "design",
        "module_decomposition", "basis_projections", "code", "unit_tests",
    ],
    approve=consensus(1, 1),
)

poc = Overlay(
    name="poc",
    on=genesis_sdlc,
    restrict_to=["intent", "requirements", "feature_decomposition", "design", "code", "unit_tests"],
    max_iter=5,
    approve=consensus(1, 1),
)

spike = Overlay(
    name="spike",
    on=genesis_sdlc,
    restrict_to=["intent", "requirements", "code", "unit_tests"],
    max_iter=2,
    approve=consensus(1, 1),
)

hotfix = Overlay(
    name="hotfix",
    on=genesis_sdlc,
    restrict_to=["design", "code", "unit_tests"],
    max_iter=3,
    approve=consensus(1, 1),
)

genesis_sdlc.overlays = [standard, poc, spike, hotfix]

if __name__ == "__main__":
    print(genesis_sdlc.describe())
