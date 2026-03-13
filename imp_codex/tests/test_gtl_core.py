# Validates: REQ-GTL-001, REQ-GTL-002, REQ-GTL-003, REQ-GTL-004, REQ-GTL-005
"""
TDD unit tests for GTL core — Genesis Topology Language object model v0.2.1.

Tests the constitutional invariants enforced at construction time:
  - Consensus: n/m validity
  - Context: locator scheme + digest prefix
  - Rule: dissent values
  - Operator: category types + URI schemes
  - Edge: confirm values, co_evolve consistency, closed operator surface
  - Overlay: approve required, restrict_to/add_* mutual exclusion
  - Package: full construction + validation + describe() + to_mermaid()

Also exercises the example packages (obligations, sdlc) as integration smoke tests.
"""

import sys
import pathlib
import pytest

# ── path setup ────────────────────────────────────────────────────────────────
# imp_codex/code must be on sys.path so `gtl.core` is importable.
# pyproject.toml adds it via pythonpath; this guard handles direct invocation.
_GTL_CODE = pathlib.Path(__file__).parents[2] / "code"
if str(_GTL_CODE) not in sys.path:
    sys.path.insert(0, str(_GTL_CODE))

from gtl.core import (  # noqa: E402
    Package, Asset, Edge, Operator, Rule, Context, Overlay,
    PackageSnapshot,
    F_D, F_P, F_H,
    Consensus, consensus, Operative,
    OPERATIVE_ON_APPROVED, OPERATIVE_ON_APPROVED_NOT_SUPERSEDED,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers — minimal valid objects reused across tests
# ═══════════════════════════════════════════════════════════════════════════════

def _op(name="check_op", category=F_D, uri="check://ok") -> Operator:
    return Operator(name, category, uri)


def _asset(name="A") -> Asset:
    return Asset(name=name, id_format=f"{name}-{{SEQ}}")


def _edge(name="e", source=None, target=None, using=None, **kwargs) -> Edge:
    src = source or _asset("S")
    tgt = target or _asset("T")
    ops = using if using is not None else []
    return Edge(name=name, source=src, target=tgt, using=ops, **kwargs)


def _minimal_package(name="pkg", extra_ops=None, extra_edges=None) -> Package:
    """A one-edge package that passes all validation."""
    op = _op("op1")
    a = _asset("A")
    b = _asset("B")
    e = _edge("e1", source=a, target=b, using=[op])
    return Package(
        name=name,
        assets=[a, b],
        edges=[e],
        operators=[op] + (extra_ops or []),
        rules=[],
        contexts=[],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 1. consensus()
# ═══════════════════════════════════════════════════════════════════════════════

class TestConsensus:
    def test_valid_simple(self):
        c = consensus(1, 1)
        assert c.n == 1 and c.m == 1

    def test_valid_majority(self):
        c = consensus(2, 3)
        assert c.n == 2 and c.m == 3

    def test_valid_unanimous(self):
        c = consensus(4, 4)
        assert c.n == c.m == 4

    def test_invalid_n_zero(self):
        with pytest.raises(ValueError):
            consensus(0, 3)

    def test_invalid_m_zero(self):
        with pytest.raises(ValueError):
            consensus(1, 0)

    def test_invalid_n_greater_than_m(self):
        with pytest.raises(ValueError):
            consensus(4, 3)

    def test_repr(self):
        assert repr(consensus(2, 3)) == "consensus(2/3)"

    def test_frozen(self):
        c = consensus(1, 2)
        with pytest.raises(Exception):
            c.n = 99  # type: ignore[misc]


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Operative
# ═══════════════════════════════════════════════════════════════════════════════

class TestOperative:
    def test_default_approved(self):
        o = Operative()
        assert o.approved is True
        assert o.not_superseded is False

    def test_both_conditions(self):
        o = Operative(approved=True, not_superseded=True)
        assert o.not_superseded is True

    def test_constants_approved(self):
        assert OPERATIVE_ON_APPROVED.approved is True
        assert OPERATIVE_ON_APPROVED.not_superseded is False

    def test_constants_approved_not_superseded(self):
        assert OPERATIVE_ON_APPROVED_NOT_SUPERSEDED.approved is True
        assert OPERATIVE_ON_APPROVED_NOT_SUPERSEDED.not_superseded is True

    def test_repr_approved_only(self):
        assert repr(OPERATIVE_ON_APPROVED) == "approved"

    def test_repr_both(self):
        assert repr(OPERATIVE_ON_APPROVED_NOT_SUPERSEDED) == "approved and not superseded"

    def test_frozen(self):
        with pytest.raises(Exception):
            OPERATIVE_ON_APPROVED.approved = False  # type: ignore[misc]


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Context
# ═══════════════════════════════════════════════════════════════════════════════

class TestContext:
    def _valid(self, scheme="git://") -> Context:
        return Context(
            name="ctx",
            locator=f"{scheme}github.com/org/repo//file.yml@abc123",
            digest="sha256:deadbeef",
        )

    @pytest.mark.parametrize("scheme", ["git://", "workspace://", "event://", "registry://"])
    def test_valid_schemes(self, scheme):
        ctx = self._valid(scheme)
        assert ctx.locator.startswith(scheme)

    def test_invalid_scheme(self):
        with pytest.raises(ValueError, match="known scheme"):
            Context(name="x", locator="http://bad", digest="sha256:abc")

    def test_invalid_digest_prefix(self):
        with pytest.raises(ValueError, match="sha256:"):
            Context(name="x", locator="git://ok", digest="md5:bad")

    def test_valid_digest_accepted(self):
        ctx = Context(name="x", locator="git://ok", digest="sha256:abc123")
        assert ctx.digest == "sha256:abc123"


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Rule
# ═══════════════════════════════════════════════════════════════════════════════

class TestRule:
    @pytest.mark.parametrize("dissent", ["required", "recorded", "none"])
    def test_valid_dissent(self, dissent):
        r = Rule("r", approve=consensus(1, 1), dissent=dissent)
        assert r.dissent == dissent

    def test_invalid_dissent(self):
        with pytest.raises(ValueError, match="dissent"):
            Rule("r", approve=consensus(1, 1), dissent="optional")

    def test_default_dissent_none(self):
        r = Rule("r", approve=consensus(1, 1))
        assert r.dissent == "none"

    def test_provisional_flag(self):
        r = Rule("r", approve=consensus(3, 4), dissent="required", provisional=True)
        assert r.provisional is True


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Operator
# ═══════════════════════════════════════════════════════════════════════════════

class TestOperator:
    @pytest.mark.parametrize("category", [F_D, F_P, F_H])
    def test_valid_categories(self, category):
        op = Operator("op", category, "check://ok")
        assert op.category is category

    def test_invalid_category(self):
        with pytest.raises(TypeError, match="F_D, F_P, or F_H"):
            Operator("op", str, "check://ok")  # type: ignore[arg-type]

    @pytest.mark.parametrize("uri", [
        "agent://some-agent",
        "exec://python -m pytest",
        "check://coverage >= 80",
        "metric://p99 < 200ms",
        "fh://single",
    ])
    def test_valid_uri_schemes(self, uri):
        op = Operator("op", F_D, uri)
        assert op.uri == uri

    def test_invalid_uri_scheme(self):
        with pytest.raises(ValueError, match="known scheme"):
            Operator("op", F_D, "http://bad")


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Asset
# ═══════════════════════════════════════════════════════════════════════════════

class TestAsset:
    def test_minimal_construction(self):
        a = Asset(name="X", id_format="X-{SEQ}")
        assert a.name == "X"
        assert a.lineage == []
        assert a.markov == []
        assert a.operative is None

    def test_lineage_is_independent(self):
        a = Asset(name="A", id_format="A-{SEQ}")
        b = Asset(name="B", id_format="B-{SEQ}", lineage=[a])
        c = Asset(name="C", id_format="C-{SEQ}", lineage=[a])
        b.lineage.append(c)
        assert c not in a.lineage  # mutable but independent instances

    def test_operative_stored(self):
        a = Asset(name="A", id_format="A-{SEQ}", operative=OPERATIVE_ON_APPROVED)
        assert a.operative is OPERATIVE_ON_APPROVED

    def test_markov_stored(self):
        a = Asset(name="A", id_format="A-{SEQ}", markov=["s1", "s2"])
        assert a.markov == ["s1", "s2"]


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Edge
# ═══════════════════════════════════════════════════════════════════════════════

class TestEdge:
    @pytest.mark.parametrize("confirm", ["question", "markov", "hypothesis"])
    def test_valid_confirm_values(self, confirm):
        e = _edge(confirm=confirm)
        assert e.confirm == confirm

    def test_invalid_confirm(self):
        with pytest.raises(ValueError, match="confirm"):
            _edge(confirm="vote")

    def test_default_confirm_markov(self):
        e = _edge()
        assert e.confirm == "markov"

    def test_co_evolve_requires_list_source(self):
        a = _asset("A")
        b = _asset("B")
        with pytest.raises(ValueError, match="co_evolve"):
            Edge(name="e", source=a, target=b, co_evolve=True)

    def test_co_evolve_with_list_source(self):
        a = _asset("A")
        b = _asset("B")
        c = _asset("C")
        e = Edge(name="e", source=[a, b], target=c, co_evolve=True)
        assert e.co_evolve is True

    def test_product_arrow_list_source(self):
        a = _asset("A")
        b = _asset("B")
        c = _asset("C")
        e = Edge(name="e", source=[a, b], target=c)
        assert isinstance(e.source, list)
        assert len(e.source) == 2

    def test_context_stored(self):
        ctx = Context(name="c", locator="git://ok", digest="sha256:abc")
        e = _edge(context=[ctx])
        assert ctx in e.context

    def test_rule_optional(self):
        e = _edge()
        assert e.rule is None


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Overlay
# ═══════════════════════════════════════════════════════════════════════════════

class TestOverlay:
    def test_restriction_overlay(self):
        pkg = _minimal_package()
        ov = Overlay(
            name="slim",
            on=pkg,
            restrict_to=["A", "B"],
            approve=consensus(1, 1),
        )
        assert ov.restrict_to == ["A", "B"]

    def test_additive_overlay(self):
        pkg = _minimal_package()
        new_op = _op("new_op")
        ov = Overlay(
            name="extended",
            on=pkg,
            add_operators=[new_op],
            approve=consensus(1, 1),
        )
        assert new_op in ov.add_operators

    def test_approve_required(self):
        pkg = _minimal_package()
        with pytest.raises(ValueError, match="approve"):
            Overlay(name="bad", on=pkg)

    def test_restrict_and_add_mutually_exclusive(self):
        pkg = _minimal_package()
        new_op = _op("x")
        with pytest.raises(ValueError, match="mutually exclusive"):
            Overlay(
                name="conflict",
                on=pkg,
                restrict_to=["A"],
                add_operators=[new_op],
                approve=consensus(1, 1),
            )

    def test_max_iter(self):
        pkg = _minimal_package()
        ov = Overlay(name="o", on=pkg, restrict_to=["A"], max_iter=3, approve=consensus(1, 1))
        assert ov.max_iter == 3


# ═══════════════════════════════════════════════════════════════════════════════
# 9. PackageSnapshot
# ═══════════════════════════════════════════════════════════════════════════════

class TestPackageSnapshot:
    def _snap(self) -> PackageSnapshot:
        return PackageSnapshot(
            snapshot_id="snap-test-v1.0",
            package_name="test_pkg",
            version="1.0",
            activated_at="2026-03-14T00:00:00Z",
            activated_by="governance-event-001",
        )

    def test_to_dict_event_type(self):
        d = self._snap().to_dict()
        assert d["event_type"] == "package_snapshot_activated"

    def test_to_dict_fields(self):
        d = self._snap().to_dict()
        assert d["snapshot_id"] == "snap-test-v1.0"
        assert d["package_name"] == "test_pkg"
        assert d["version"] == "1.0"

    def test_work_binding(self):
        wb = self._snap().work_binding()
        assert wb["package_snapshot_id"] == "snap-test-v1.0"
        assert wb["package_name"] == "test_pkg"
        assert len(wb) == 2  # only two fields


# ═══════════════════════════════════════════════════════════════════════════════
# 10. Package — construction and validation
# ═══════════════════════════════════════════════════════════════════════════════

class TestPackageConstruction:
    def test_minimal_package_constructs(self):
        pkg = _minimal_package()
        assert pkg.name == "pkg"
        assert len(pkg.assets) == 2
        assert len(pkg.edges) == 1
        assert len(pkg.operators) == 1

    def test_undeclared_operator_rejected(self):
        op_declared = _op("declared")
        op_sneaked  = _op("sneaked")
        a = _asset("A")
        b = _asset("B")
        e = Edge(name="e", source=a, target=b, using=[op_sneaked])
        with pytest.raises(ValueError, match="not declared in package"):
            Package(
                name="bad",
                assets=[a, b],
                edges=[e],
                operators=[op_declared],  # sneaked not listed here
            )

    def test_all_edge_operators_must_be_declared(self):
        op1 = _op("op1")
        op2 = _op("op2")
        a = _asset("A")
        b = _asset("B")
        e = Edge(name="e", source=a, target=b, using=[op1, op2])
        with pytest.raises(ValueError):
            Package(name="bad", assets=[a, b], edges=[e], operators=[op1])  # op2 missing

    def test_co_evolve_without_list_source_rejected_by_edge(self):
        # Edge itself guards this — package doesn't need to re-check
        a = _asset("A")
        b = _asset("B")
        with pytest.raises(ValueError, match="co_evolve"):
            Edge(name="e", source=a, target=b, co_evolve=True)

    def test_empty_package_constructs(self):
        pkg = Package(name="empty")
        assert pkg.assets == []
        assert pkg.edges == []


# ═══════════════════════════════════════════════════════════════════════════════
# 11. Package.describe()
# ═══════════════════════════════════════════════════════════════════════════════

class TestPackageDescribe:
    def test_contains_package_name(self):
        pkg = _minimal_package("my_pkg")
        desc = pkg.describe()
        assert "my_pkg" in desc

    def test_contains_asset_names(self):
        pkg = _minimal_package()
        desc = pkg.describe()
        assert "A" in desc
        assert "B" in desc

    def test_contains_edge_name(self):
        pkg = _minimal_package()
        desc = pkg.describe()
        assert "e1" in desc

    def test_arrow_single_source(self):
        pkg = _minimal_package()
        desc = pkg.describe()
        assert "->" in desc

    def test_coevolve_arrow(self):
        op = _op("op1")
        a = _asset("A")
        b = _asset("B")
        e = Edge(name="tdd", source=[a, b], target=b, using=[op], co_evolve=True)
        pkg = Package(name="p", assets=[a, b], edges=[e], operators=[op])
        desc = pkg.describe()
        assert "<->" in desc

    def test_overlays_section_when_present(self):
        pkg = _minimal_package()
        ov = Overlay(name="slim", on=pkg, restrict_to=["A"], approve=consensus(1, 1))
        pkg.overlays = [ov]
        desc = pkg.describe()
        assert "slim" in desc


# ═══════════════════════════════════════════════════════════════════════════════
# 12. Package.to_mermaid()
# ═══════════════════════════════════════════════════════════════════════════════

class TestPackageMermaid:
    def test_returns_mermaid_fenced_block(self):
        pkg = _minimal_package()
        m = pkg.to_mermaid()
        assert m.startswith("```mermaid")
        assert m.endswith("```")

    def test_contains_asset_nodes(self):
        pkg = _minimal_package()
        m = pkg.to_mermaid()
        assert "A" in m
        assert "B" in m

    def test_contains_edge_arrow(self):
        pkg = _minimal_package()
        m = pkg.to_mermaid()
        assert "-->" in m

    def test_restriction_overlay_filters_nodes(self):
        op = _op("op1")
        a = _asset("A")
        b = _asset("B")
        c = _asset("C")
        e1 = Edge(name="e1", source=a, target=b, using=[op])
        e2 = Edge(name="e2", source=b, target=c, using=[op])
        pkg = Package(name="p", assets=[a, b, c], edges=[e1, e2], operators=[op])
        ov = Overlay(name="slim", on=pkg, restrict_to=["A", "B"], approve=consensus(1, 1))
        m = pkg.to_mermaid(overlay=ov)
        # C should not appear since it's outside the overlay
        lines = m.splitlines()
        # No line should reference C as a node definition
        node_lines = [l for l in lines if '"C"' in l and "C[" in l]
        assert not node_lines, "C node should be filtered by restrict_to overlay"

    def test_product_arrow_join_node(self):
        op = _op("op1")
        a = _asset("A")
        b = _asset("B")
        c = _asset("C")
        e = Edge(name="apply", source=[a, b], target=c, using=[op])
        pkg = Package(name="p", assets=[a, b, c], edges=[e], operators=[op])
        m = pkg.to_mermaid()
        assert "join_" in m  # join node synthesised for product arrows

    def test_governed_edge_gets_class(self):
        op = _op("op1")
        rule = Rule("r", approve=consensus(1, 1))
        a = _asset("A")
        b = _asset("B")
        e = Edge(name="e", source=a, target=b, using=[op], rule=rule)
        pkg = Package(name="p", assets=[a, b], edges=[e], operators=[op], rules=[rule])
        m = pkg.to_mermaid()
        assert "governed" in m

    def test_co_evolve_edge_gets_class(self):
        op = _op("op1")
        a = _asset("A")
        b = _asset("B")
        e = Edge(name="tdd", source=[a, b], target=b, using=[op], co_evolve=True)
        pkg = Package(name="p", assets=[a, b], edges=[e], operators=[op])
        m = pkg.to_mermaid()
        assert "coevolve" in m
        assert "<-->" in m

    def test_operative_asset_shown_with_label(self):
        op = _op("op1")
        a = Asset(name="A", id_format="A-{SEQ}", operative=OPERATIVE_ON_APPROVED)
        b = _asset("B")
        e = Edge(name="e", source=a, target=b, using=[op])
        pkg = Package(name="p", assets=[a, b], edges=[e], operators=[op])
        m = pkg.to_mermaid()
        assert "operative" in m


# ═══════════════════════════════════════════════════════════════════════════════
# 13. Integration — example packages import and construct without error
# ═══════════════════════════════════════════════════════════════════════════════

class TestExamplePackages:
    def test_obligations_package_constructs(self):
        """genesis_obligations imports cleanly and passes Package validation."""
        from gtl.examples.obligations import genesis_obligations
        assert genesis_obligations.name == "genesis_obligations"
        assert len(genesis_obligations.assets) > 0
        assert len(genesis_obligations.edges) > 0

    def test_sdlc_package_constructs(self):
        """genesis_sdlc imports cleanly and passes Package validation."""
        from gtl.examples.sdlc import genesis_sdlc
        assert genesis_sdlc.name == "genesis_sdlc"
        assert len(genesis_sdlc.assets) > 0
        assert len(genesis_sdlc.edges) > 0

    def test_sdlc_has_co_evolve_edge(self):
        from gtl.examples.sdlc import genesis_sdlc
        co_edges = [e for e in genesis_sdlc.edges if e.co_evolve]
        assert len(co_edges) >= 1, "genesis_sdlc should have at least one co-evolve edge (TDD)"

    def test_sdlc_profiles_are_restriction_overlays(self):
        from gtl.examples.sdlc import genesis_sdlc, standard, poc, spike, hotfix
        for ov in [standard, poc, spike, hotfix]:
            assert ov.restrict_to is not None
            assert ov.approve is not None

    def test_obligations_has_product_arrow(self):
        from gtl.examples.obligations import apply
        assert isinstance(apply.source, list), "apply edge should be a product arrow"

    def test_sdlc_describe_runs(self):
        from gtl.examples.sdlc import genesis_sdlc
        desc = genesis_sdlc.describe()
        assert "genesis_sdlc" in desc

    def test_sdlc_to_mermaid_runs(self):
        from gtl.examples.sdlc import genesis_sdlc
        m = genesis_sdlc.to_mermaid()
        assert "```mermaid" in m

    def test_obligations_to_mermaid_runs(self):
        from gtl.examples.obligations import genesis_obligations
        m = genesis_obligations.to_mermaid()
        assert "```mermaid" in m

    def test_sdlc_mermaid_with_poc_overlay(self):
        from gtl.examples.sdlc import genesis_sdlc, poc
        m = genesis_sdlc.to_mermaid(overlay=poc)
        assert "```mermaid" in m
        # uat_tests is excluded from poc profile — should not appear as a node
        assert '"uat tests"' not in m.lower() or "uat_tests" not in m
