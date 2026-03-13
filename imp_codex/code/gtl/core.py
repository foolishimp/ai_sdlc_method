"""
GTL constitutional object model — v0.2

Python library as the authored surface. No custom DSL parser.
AI assembles packages from this library; humans audit via to_mermaid().

No external dependencies. Dataclasses + stdlib only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Optional


# ── Functor categories ─────────────────────────────────────────────────────

class F_D:  """Deterministic — zero ambiguity, pass/fail."""
class F_P:  """Probabilistic — agent/LLM, bounded ambiguity."""
class F_H:  """Human — persistent ambiguity, judgment required."""


# ── Approval vocabulary ────────────────────────────────────────────────────

@dataclass(frozen=True)
class Consensus:
    n: int
    m: int

    def __post_init__(self):
        if self.n < 1 or self.m < 1 or self.n > self.m:
            raise ValueError(f"consensus({self.n}/{self.m}): n must be 1..m")

    def __repr__(self):
        return f"consensus({self.n}/{self.m})"

def consensus(n: int, m: int) -> Consensus:
    return Consensus(n, m)


# ── Core constructs ────────────────────────────────────────────────────────

@dataclass
class Rule:
    name: str
    approve: Consensus
    dissent: str = "none"       # "required" | "recorded" | "none"
    provisional: bool = False

    def __post_init__(self):
        if self.dissent not in ("required", "recorded", "none"):
            raise ValueError(f"Rule.dissent must be required|recorded|none, got {self.dissent!r}")


@dataclass
class Operator:
    name: str
    category: type              # F_D | F_P | F_H
    uri: str

    def __post_init__(self):
        if self.category not in (F_D, F_P, F_H):
            raise TypeError(f"Operator.category must be F_D, F_P, or F_H")
        for scheme in ("agent://", "exec://", "check://", "metric://", "fh://"):
            if self.uri.startswith(scheme):
                break
        else:
            raise ValueError(f"Operator URI must use a known scheme (agent://, exec://, check://, metric://, fh://): {self.uri!r}")


@dataclass
class Context:
    name: str
    from_git: str
    digest: str

    def __post_init__(self):
        if not self.digest.startswith("sha256:"):
            raise ValueError(f"Context.digest must start with 'sha256:': {self.digest!r}")


@dataclass
class Asset:
    name: str
    id_format: str
    lineage: list[Asset] = field(default_factory=list)
    markov: list[str] = field(default_factory=list)
    operative: Optional[str] = None     # e.g. "approved and not superseded"


@dataclass
class Edge:
    name: str
    source: Asset | list[Asset]         # list = product arrow A × B × ...
    target: Asset
    using: list[Operator] = field(default_factory=list)
    confirm: str = "markov"             # "question" | "markov" | "hypothesis"
    rule: Optional[Rule] = None
    context: list[Context] = field(default_factory=list)
    co_evolve: bool = False             # True only for <-> bidirectional edges

    def __post_init__(self):
        if self.confirm not in ("question", "markov", "hypothesis"):
            raise ValueError(f"Edge.confirm must be question|markov|hypothesis, got {self.confirm!r}")
        # co_evolve only makes sense for bidirectional (source == target effectively)
        # We track it as a flag; the package validator checks operator surface


@dataclass
class Overlay:
    name: str
    on: "Package"
    restrict_to: Optional[list[str]] = None    # names of assets/edges to keep
    add_assets: list[Asset] = field(default_factory=list)
    add_edges: list[Edge] = field(default_factory=list)
    add_operators: list[Operator] = field(default_factory=list)
    add_rules: list[Rule] = field(default_factory=list)
    add_contexts: list[Context] = field(default_factory=list)
    max_iter: Optional[int] = None
    approve: Optional[Consensus] = None

    def __post_init__(self):
        if self.approve is None:
            raise ValueError(f"Overlay '{self.name}' must declare approve=consensus(n/m)")
        if self.restrict_to is not None and any([
            self.add_assets, self.add_edges, self.add_operators,
            self.add_rules, self.add_contexts
        ]):
            raise ValueError(f"Overlay '{self.name}': restrict_to and add_* are mutually exclusive")


@dataclass
class Package:
    name: str
    assets: list[Asset] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    operators: list[Operator] = field(default_factory=list)
    rules: list[Rule] = field(default_factory=list)
    contexts: list[Context] = field(default_factory=list)
    overlays: list[Overlay] = field(default_factory=list)

    def __post_init__(self):
        self._validate()

    def _validate(self):
        errors = []
        declared_ops = {op.name for op in self.operators}
        declared_rules = {r.name for r in self.rules}

        for edge in self.edges:
            # 1. Closed operator surface
            for op in edge.using:
                if op.name not in declared_ops:
                    errors.append(f"Edge '{edge.name}': operator '{op.name}' not declared in package")

            # 2. Single approval authority — rule is present, no inline approve needed
            # (In Python model there's no separate 'approve' on edge — rule IS the authority.
            # This invariant is enforced by the object model: edge.rule is the only path.)

            # 3. co_evolve consistency
            if edge.co_evolve and not isinstance(edge.source, list):
                errors.append(f"Edge '{edge.name}': co_evolve=True requires source to be a list [A, B]")

        # 4. Context digests (already enforced in Context.__post_init__)

        if errors:
            raise ValueError("Package validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    def describe(self) -> str:
        lines = [f"Package: {self.name}"]
        lines.append(f"  assets    ({len(self.assets)}): " + ", ".join(a.name for a in self.assets))
        lines.append(f"  operators ({len(self.operators)}): " + ", ".join(o.name for o in self.operators))
        lines.append(f"  rules     ({len(self.rules)}): " + ", ".join(r.name for r in self.rules))
        lines.append(f"  contexts  ({len(self.contexts)}): " + ", ".join(c.name for c in self.contexts))
        lines.append(f"  edges     ({len(self.edges)}):")
        for e in self.edges:
            src = (
                " × ".join(a.name for a in e.source)
                if isinstance(e.source, list)
                else e.source.name
            )
            arrow = "<->" if e.co_evolve else "->"
            gov = f"  [govern: {e.rule.name}]" if e.rule else ""
            ops = ", ".join(o.name for o in e.using)
            lines.append(f"    {e.name}: {src} {arrow} {e.target.name}  confirm={e.confirm}{gov}")
            lines.append(f"      using: {ops}")
        if self.overlays:
            lines.append(f"  overlays  ({len(self.overlays)}):")
            for ov in self.overlays:
                if ov.restrict_to:
                    lines.append(f"    {ov.name}: restrict to [{', '.join(ov.restrict_to)}] max_iter={ov.max_iter}")
                else:
                    lines.append(f"    {ov.name}: additive")
        return "\n".join(lines)

    def to_mermaid(self, overlay: Optional["Overlay"] = None) -> str:
        """Render the package topology as a Mermaid flowchart.

        If an overlay with restrict_to is supplied, only those assets/edges are shown.
        This is the human audit surface — generated from the object model, never authored.
        """
        active_asset_names: Optional[set[str]] = None
        if overlay and overlay.restrict_to:
            active_asset_names = set(overlay.restrict_to)

        def _node(a: Asset) -> str:
            label = a.name.replace("_", " ")
            if a.operative:
                return f'  {a.name}(["{label}\\noperative: {a.operative}"])'
            return f'  {a.name}["{label}"]'

        def _visible(a: Asset) -> bool:
            return active_asset_names is None or a.name in active_asset_names

        lines = ["```mermaid", f"graph LR"]

        # Style classes
        lines.append("  classDef governed fill:#ffeeba,stroke:#d4a017")
        lines.append("  classDef product  fill:#d4edda,stroke:#28a745")
        lines.append("  classDef coevolve fill:#cce5ff,stroke:#004085")

        # Nodes
        for a in self.assets:
            if _visible(a):
                lines.append(_node(a))

        # Edges
        for e in self.edges:
            sources = e.source if isinstance(e.source, list) else [e.source]
            if not all(_visible(s) for s in sources) or not _visible(e.target):
                continue

            gov_label = f"|{e.rule.name}|" if e.rule else ""
            confirm_label = f" [{e.confirm}]"
            ops_label = ", ".join(o.name for o in e.using[:2])  # first 2 ops for brevity
            if len(e.using) > 2:
                ops_label += f" +{len(e.using)-2}"
            edge_label = f"|{ops_label}{confirm_label}|"

            if e.co_evolve:
                # bidirectional — render as two arrows
                a, b = sources[0], sources[1]
                lines.append(f"  {a.name} <-->|co_evolve| {b.name}")
                lines.append(f"  {a.name}:::coevolve")
                lines.append(f"  {b.name}:::coevolve")
            elif len(sources) > 1:
                # product arrow: synthetic join node
                join = "join_" + "_".join(s.name for s in sources)
                join_label = " × ".join(s.name for s in sources)
                lines.append(f'  {join}(("{join_label}"))')
                for s in sources:
                    lines.append(f"  {s.name} --> {join}")
                lines.append(f"  {join} --{edge_label}--> {e.target.name}")
                lines.append(f"  {join}:::product")
            else:
                src = sources[0]
                arrow = f"--{edge_label}-->"
                if e.rule:
                    lines.append(f"  {src.name} {arrow} {e.target.name}")
                    lines.append(f"  {e.target.name}:::governed")
                else:
                    lines.append(f"  {src.name} {arrow} {e.target.name}")

        title = self.name
        if overlay:
            title += f" [{overlay.name}]"
        lines.append(f"  subgraph \" \"")
        lines.append(f"    direction LR")
        lines.append(f"  end")
        lines.append("```")
        return "\n".join(lines)
