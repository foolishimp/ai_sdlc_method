# Implements: REQ-F-ENGINE-001, REQ-F-LIFE-001, REQ-F-EVENT-001, REQ-F-UX-001
"""Executable Codex runtime primitives for the methodology tenant."""

from .commands import (
    gen_comment,
    gen_consensus_close,
    gen_consensus_open,
    gen_consensus_recover,
    gen_consensus_status,
    gen_dispatch_intents,
    gen_dispose,
    gen_checkpoint,
    gen_init,
    gen_fold_back,
    gen_gaps,
    gen_iterate,
    gen_propose,
    gen_release,
    gen_review,
    gen_spec_modify,
    gen_spawn,
    gen_start,
    gen_status,
    gen_trace,
    gen_vote,
)
from .consensus_observer import ConsensusObserverResult, run_consensus_observer
from .edge_runner import DispatchTarget, EdgeRunResult, run_edge
from .events import append_run_event, load_events
from .fp_worker import FpWorkResult, run_fp_work, run_pending_fp_work
from .intent_observer import IntentObserverResult, run_intent_observer
from .paths import RuntimePaths, bootstrap_workspace
from .workspace_analysis import WorkspaceAnalysisResult, WorkspaceAsset, build_workspace_asset, run_workspace_analysis

__all__ = [
    "DispatchTarget",
    "EdgeRunResult",
    "FpWorkResult",
    "IntentObserverResult",
    "ConsensusObserverResult",
    "RuntimePaths",
    "WorkspaceAnalysisResult",
    "WorkspaceAsset",
    "append_run_event",
    "build_workspace_asset",
    "bootstrap_workspace",
    "gen_comment",
    "gen_checkpoint",
    "gen_consensus_close",
    "gen_consensus_open",
    "run_consensus_observer",
    "gen_consensus_recover",
    "gen_consensus_status",
    "gen_dispatch_intents",
    "gen_dispose",
    "gen_init",
    "gen_fold_back",
    "gen_gaps",
    "gen_iterate",
    "gen_propose",
    "gen_release",
    "gen_review",
    "gen_spec_modify",
    "gen_spawn",
    "gen_start",
    "gen_status",
    "gen_trace",
    "gen_vote",
    "load_events",
    "run_fp_work",
    "run_pending_fp_work",
    "run_edge",
    "run_intent_observer",
    "run_workspace_analysis",
]
