import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from .f_probabilistic import GeminiFunctor
from ..engine.models import FunctorResult, Outcome

class ConsensusFunctor(GeminiFunctor):
    """CONSENSUS Functor (ADR-S-025).
    Manages multi-stakeholder evaluation with quorum rules.
    """
    
    def evaluate(self, candidate: str, context: Dict[str, Any]) -> FunctorResult:
        """Execute the CONSENSUS process: collect votes, evaluate quorum, check dispositions."""
        
        roster = context.get("roster", [])
        quorum_config = context.get("quorum", {"threshold": "majority"})
        min_duration = context.get("min_duration", "P0D")
        
        # Load current vote/comment state from context (persisted in vector)
        votes = context.get("votes", [])
        comments = context.get("comments", [])
        published_at = context.get("published_at")
        
        if not published_at:
            # First iteration — initialize consensus window
            return FunctorResult(
                name="consensus",
                outcome=Outcome.SKIP,
                delta=1,
                reasoning="Consensus window not yet opened. Publishing proposal to roster.",
                metadata={
                    "status": "published",
                    "published_at": datetime.now(timezone.utc).isoformat(),
                    "roster": roster,
                    "quorum": quorum_config
                }
            )

        # Quorum Calculation
        approve_votes = [v for v in votes if v.get("verdict") == "approve"]
        reject_votes = [v for v in votes if v.get("verdict") == "reject"]
        abstain_votes = [v for v in votes if v.get("verdict") == "abstain"]
        veto_cast = any(v.get("verdict") == "reject" for v in votes if v.get("role") == "veto_holder")
        
        # Neutral abstention model: approve / (approve + reject)
        total_cast = len(approve_votes) + len(reject_votes)
        approve_ratio = approve_votes / total_cast if total_cast > 0 else 0.0
        
        # Participation check (ADR-GG-018 requirement: 50% threshold)
        participation_rate = len(votes) / len(roster) if len(roster) > 0 else 1.0
        
        threshold_map = {"majority": 0.5, "supermajority": 0.66, "unanimity": 1.0}
        required_ratio = threshold_map.get(quorum_config["threshold"], 0.5)
        
        quorum_reached = (approve_ratio >= required_ratio) and (participation_rate >= 0.5)
        
        # Comment Dispositions
        undispositioned = [c for c in comments if c.get("disposition") is None]
        
        if veto_cast:
            return FunctorResult(
                name="consensus",
                outcome=Outcome.FAIL,
                delta=1,
                reasoning="CONSENSUS FAILED: Veto exercised by authorized holder.",
                metadata={"failure_reason": "veto_exercised"}
            )
            
        if quorum_reached and not undispositioned:
            return FunctorResult(
                name="consensus",
                outcome=Outcome.PASS,
                delta=0,
                reasoning=f"CONSENSUS REACHED: Approve ratio {approve_ratio:.2f} satisfies {quorum_config['threshold']} threshold.",
                metadata={"approve_ratio": approve_ratio, "participation": participation_rate}
            )
            
        # If not reached, route to interactive sub-agent for vote collection
        return super().evaluate(candidate, {
            **context,
            "status": "under_review",
            "approve_ratio": approve_ratio,
            "undispositioned_comments": len(undispositioned)
        })
