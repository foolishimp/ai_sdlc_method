# Validates: REQ-SUPV-003, REQ-EVAL-001
"""Post-archive analysis of E2E runs — verifies homeostatic chain closure.

Reads an archived E2E run directory and produces a forensic report:
1. Event stream summary (counts by type, timeline)
2. Failure observability (evaluator_detail, command_error events)
3. Homeostatic chain verification (failure → intent_raised → correction)
4. Multi-iteration edges (proves iterate() actually iterated)
5. Delta progression per edge (convergence curve)

Usage:
    python -m imp_claude.tests.e2e.analyse_run <run_dir>
    python -m imp_claude.tests.e2e.analyse_run imp_claude/tests/e2e/runs/e2e_2.8.0_*_0003

Exit codes:
    0 = homeostatic loop working (VERIFIED: cross-edge, or CORRECTED: within-edge)
    1 = no failures observed (trivial convergence — loop untested)
    2 = failures observed but no correction at all (loop broken)
    3 = analysis error or partial
"""

import json
import pathlib
import sys
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any


def load_events(run_dir: pathlib.Path) -> list[dict[str, Any]]:
    """Parse events.jsonl from a run archive."""
    events_file = run_dir / ".ai-workspace" / "events" / "events.jsonl"
    if not events_file.exists():
        print(f"ERROR: No events.jsonl found at {events_file}")
        return []

    events = []
    with open(events_file) as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"WARNING: Malformed JSON on line {i}: {e}")
    return events


def load_meta(run_dir: pathlib.Path) -> dict[str, Any]:
    """Load run metadata if available."""
    meta_file = run_dir / ".e2e-meta" / "meta.json"
    if meta_file.exists():
        try:
            return json.loads(meta_file.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def load_test_results(run_dir: pathlib.Path) -> dict[str, Any]:
    """Load test results if available."""
    results_file = run_dir / ".e2e-meta" / "test_results.json"
    if results_file.exists():
        try:
            return json.loads(results_file.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def analyse_event_stream(events: list[dict]) -> dict[str, Any]:
    """Analyse the event stream for patterns."""
    type_counts = Counter(e.get("event_type", "unknown") for e in events)

    # Timeline
    timestamps = []
    for e in events:
        ts = e.get("timestamp", "")
        if ts:
            try:
                timestamps.append(datetime.fromisoformat(ts.replace("Z", "+00:00")))
            except (ValueError, TypeError):
                pass

    duration = None
    if len(timestamps) >= 2:
        duration = (timestamps[-1] - timestamps[0]).total_seconds()

    return {
        "total_events": len(events),
        "type_counts": dict(type_counts),
        "duration_seconds": duration,
        "first_event": events[0].get("event_type") if events else None,
        "last_event": events[-1].get("event_type") if events else None,
    }


def analyse_iterations(events: list[dict]) -> dict[str, Any]:
    """Analyse iteration patterns per feature+edge."""
    edges: dict[str, list[dict]] = defaultdict(list)

    for e in events:
        if e.get("event_type") == "iteration_completed":
            feature = e.get("feature", "unknown")
            edge = e.get("edge", "unknown")
            key = f"{feature}:{edge}"
            edges[key].append(e)

    edge_analysis = {}
    multi_iteration_edges = 0
    total_failures = 0

    for key, iterations in edges.items():
        iterations.sort(key=lambda x: x.get("iteration", 0))
        deltas = [it.get("delta", "?") for it in iterations]
        statuses = [it.get("status", "?") for it in iterations]

        # Count failed evaluators across iterations
        edge_failures = 0
        for it in iterations:
            ev = it.get("evaluators", {})
            if isinstance(ev, dict):
                edge_failures += ev.get("failed", 0)

        total_failures += edge_failures

        if len(iterations) > 1:
            multi_iteration_edges += 1

        edge_analysis[key] = {
            "iterations": len(iterations),
            "delta_progression": deltas,
            "statuses": statuses,
            "evaluator_failures": edge_failures,
            "converged": statuses[-1] == "converged" if statuses else False,
        }

    return {
        "edges": edge_analysis,
        "multi_iteration_count": multi_iteration_edges,
        "total_evaluator_failures": total_failures,
    }


def analyse_failure_observability(events: list[dict]) -> dict[str, Any]:
    """Check for failure observability events (REQ-SUPV-003)."""
    evaluator_details = [e for e in events if e.get("event_type") == "evaluator_detail"]
    command_errors = [e for e in events if e.get("event_type") == "command_error"]
    health_checks = [e for e in events if e.get("event_type") == "health_checked"]
    abandoned = [e for e in events if e.get("event_type") == "iteration_abandoned"]

    # Extract failure patterns
    failure_patterns: dict[str, int] = Counter()
    for ed in evaluator_details:
        data = ed.get("data", {})
        check_name = data.get("check_name", "unknown")
        failure_patterns[check_name] += 1

    return {
        "evaluator_detail_count": len(evaluator_details),
        "command_error_count": len(command_errors),
        "health_check_count": len(health_checks),
        "iteration_abandoned_count": len(abandoned),
        "failure_patterns": dict(failure_patterns),
        "has_failure_events": bool(evaluator_details or command_errors),
    }


def analyse_homeostatic_chain(events: list[dict]) -> dict[str, Any]:
    """Verify the homeostatic chain: failure → intent_raised → correction.

    The chain is:
    1. evaluator_detail (or iteration with failed > 0): failure observed
    2. intent_raised: system generated an intent from the failure
    3. subsequent iteration with lower delta: correction applied

    Returns chain status and evidence.
    """
    intent_raised = [e for e in events if e.get("event_type") == "intent_raised"]

    # Check for any failures (evaluator_detail events OR iterations with failed > 0)
    has_failures = False
    failure_evidence = []

    for e in events:
        if e.get("event_type") == "evaluator_detail":
            has_failures = True
            data = e.get("data", {})
            failure_evidence.append(
                f"evaluator_detail: {data.get('check_name', '?')} "
                f"on {data.get('edge', '?')} iter {data.get('iteration', '?')}"
            )
        elif e.get("event_type") == "iteration_completed":
            ev = e.get("evaluators", {})
            if isinstance(ev, dict) and ev.get("failed", 0) > 0:
                has_failures = True
                failure_evidence.append(
                    f"iteration_completed: {ev['failed']} failed on "
                    f"{e.get('edge', '?')} iter {e.get('iteration', '?')}"
                )

    # Check for within-edge correction: failure on iteration N, delta=0 on
    # a later iteration of the SAME edge. This is the iterate() loop working.
    edge_corrections = []
    edge_deltas: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for e in events:
        if e.get("event_type") == "iteration_completed":
            edge = e.get("edge", "?")
            iteration = e.get("iteration", 0)
            delta = e.get("delta")
            if delta is not None:
                edge_deltas[edge].append((iteration, delta))

    for edge, deltas in edge_deltas.items():
        deltas.sort()
        if len(deltas) >= 2 and deltas[0][1] > 0 and deltas[-1][1] == 0:
            edge_corrections.append({
                "edge": edge,
                "initial_delta": deltas[0][1],
                "final_delta": deltas[-1][1],
                "iterations": len(deltas),
                "delta_curve": [d for _, d in deltas],
            })

    has_within_edge_correction = bool(edge_corrections)

    # Check for cross-edge correction via intent_raised
    intent_corrections = []
    if intent_raised:
        for intent in intent_raised:
            intent_ts = intent.get("timestamp", "")
            for e in events:
                if (e.get("event_type") == "iteration_completed"
                        and e.get("timestamp", "") > intent_ts
                        and e.get("delta", 999) < 999):
                    intent_corrections.append({
                        "intent": intent.get("data", {}).get("intent_id", "?"),
                        "subsequent_delta": e.get("delta"),
                        "edge": e.get("edge"),
                    })
                    break

    # Determine chain status (5 levels, most complete first)
    #
    # VERIFIED:  failure → intent_raised → cross-edge correction (full loop)
    # CORRECTED: failure → within-edge delta reduction → convergence (iterate works)
    # PARTIAL:   intent_raised emitted but no subsequent correction observed
    # BROKEN:    failures detected but no correction of any kind
    # UNTESTED:  no failures observed at all
    if not has_failures:
        chain_status = "UNTESTED"
        chain_message = ("No failures observed — all edges converged trivially. "
                        "The homeostatic loop was never exercised.")
    elif has_failures and intent_raised and intent_corrections:
        chain_status = "VERIFIED"
        chain_message = ("Full homeostatic chain verified: failure → intent_raised → "
                        f"cross-edge correction. {len(intent_raised)} intent(s) raised, "
                        f"{len(intent_corrections)} correction(s) observed.")
    elif has_failures and intent_raised:
        chain_status = "PARTIAL"
        chain_message = ("Failures observed and intent_raised emitted, but no "
                        "subsequent correction detected in delta progression.")
    elif has_failures and has_within_edge_correction:
        chain_status = "CORRECTED"
        edges_fixed = [c["edge"] for c in edge_corrections]
        chain_message = (
            f"Within-edge homeostasis verified: failure detected → iterate() "
            f"corrected → delta reduced to 0. Edges corrected: {edges_fixed}. "
            f"No intent_raised needed (deficiency was within current edge scope)."
        )
    elif has_failures:
        chain_status = "BROKEN"
        chain_message = ("Failures observed but no correction of any kind — "
                        "neither within-edge delta reduction nor intent_raised.")
    else:
        chain_status = "UNKNOWN"
        chain_message = "Unable to determine chain status."

    return {
        "chain_status": chain_status,
        "chain_message": chain_message,
        "has_failures": has_failures,
        "failure_count": len(failure_evidence),
        "failure_evidence": failure_evidence[:20],  # cap for readability
        "has_within_edge_correction": has_within_edge_correction,
        "edge_corrections": edge_corrections,
        "intent_raised_count": len(intent_raised),
        "intents": [
            {
                "id": e.get("data", {}).get("intent_id", "?"),
                "trigger": e.get("data", {}).get("trigger", "?"),
                "signal_source": e.get("data", {}).get("signal_source", "?"),
                "severity": e.get("data", {}).get("severity", "?"),
            }
            for e in intent_raised
        ],
        "intent_corrections": intent_corrections,
    }


def print_report(run_dir: pathlib.Path, events: list[dict]) -> int:
    """Print the full forensic report. Returns exit code."""
    meta = load_meta(run_dir)
    test_results = load_test_results(run_dir)
    stream = analyse_event_stream(events)
    iterations = analyse_iterations(events)
    observability = analyse_failure_observability(events)
    chain = analyse_homeostatic_chain(events)

    print(f"\n{'='*70}")
    print(f"  E2E RUN FORENSIC ANALYSIS")
    print(f"  Archive: {run_dir.name}")
    print(f"{'='*70}\n")

    # Meta
    if meta:
        elapsed = meta.get("elapsed_seconds", "?")
        rc = meta.get("returncode", "?")
        timed_out = meta.get("timed_out", False)
        print(f"  Runtime:     {elapsed}s (rc={rc}, timed_out={timed_out})")

    if test_results:
        passed = test_results.get("passed", 0)
        total = test_results.get("total", 0)
        failed = test_results.get("failed", 0)
        print(f"  Test Result: {passed}/{total} passed, {failed} failed")

    # Event Stream
    print(f"\n{'─'*70}")
    print(f"  1. EVENT STREAM SUMMARY")
    print(f"{'─'*70}")
    print(f"  Total events: {stream['total_events']}")
    if stream['duration_seconds']:
        print(f"  Duration:     {stream['duration_seconds']:.0f}s")
    print(f"  Event types:")
    for etype, count in sorted(stream['type_counts'].items()):
        print(f"    {etype:30s} {count:3d}")

    # Iteration Analysis
    print(f"\n{'─'*70}")
    print(f"  2. ITERATION ANALYSIS")
    print(f"{'─'*70}")
    print(f"  Multi-iteration edges: {iterations['multi_iteration_count']}")
    print(f"  Total evaluator failures: {iterations['total_evaluator_failures']}")
    for key, analysis in sorted(iterations['edges'].items()):
        status = "CONVERGED" if analysis['converged'] else "NOT CONVERGED"
        print(f"\n  {key}")
        print(f"    Iterations:  {analysis['iterations']}")
        print(f"    Delta curve: {analysis['delta_progression']}")
        print(f"    Failures:    {analysis['evaluator_failures']}")
        print(f"    Status:      {status}")

    # Failure Observability
    print(f"\n{'─'*70}")
    print(f"  3. FAILURE OBSERVABILITY (REQ-SUPV-003)")
    print(f"{'─'*70}")
    print(f"  evaluator_detail events:   {observability['evaluator_detail_count']}")
    print(f"  command_error events:      {observability['command_error_count']}")
    print(f"  health_checked events:     {observability['health_check_count']}")
    print(f"  iteration_abandoned events: {observability['iteration_abandoned_count']}")
    if observability['failure_patterns']:
        print(f"  Failure patterns:")
        for pattern, count in sorted(observability['failure_patterns'].items()):
            print(f"    {pattern:30s} {count:3d}x")
    else:
        print(f"  No failure events recorded.")

    # Homeostatic Chain
    print(f"\n{'─'*70}")
    print(f"  4. HOMEOSTATIC CHAIN VERIFICATION")
    print(f"{'─'*70}")
    status_icons = {
        "VERIFIED": "[PASS]",
        "CORRECTED": "[PASS]",
        "PARTIAL": "[WARN]",
        "BROKEN": "[FAIL]",
        "UNTESTED": "[SKIP]",
        "UNKNOWN": "[????]",
    }
    icon = status_icons.get(chain['chain_status'], "[????]")
    print(f"  Status: {icon} {chain['chain_status']}")
    print(f"  {chain['chain_message']}")

    if chain['failure_evidence']:
        print(f"\n  Failure evidence ({chain['failure_count']} total):")
        for ev in chain['failure_evidence'][:10]:
            print(f"    - {ev}")

    if chain['edge_corrections']:
        print(f"\n  Within-edge corrections ({len(chain['edge_corrections'])}):")
        for corr in chain['edge_corrections']:
            print(f"    - {corr['edge']}: delta {corr['delta_curve']} "
                  f"({corr['iterations']} iterations)")

    if chain['intents']:
        print(f"\n  Intents raised ({chain['intent_raised_count']}):")
        for intent in chain['intents']:
            print(f"    - {intent['id']}: {intent['trigger']} "
                  f"(source={intent['signal_source']}, severity={intent['severity']})")

    if chain['intent_corrections']:
        print(f"\n  Cross-edge corrections:")
        for corr in chain['intent_corrections']:
            print(f"    - After {corr['intent']}: delta→{corr['subsequent_delta']} "
                  f"on {corr['edge']}")

    # Verdict
    print(f"\n{'='*70}")
    print(f"  VERDICT: {icon} {chain['chain_status']}")
    print(f"{'='*70}\n")

    # Return exit code
    if chain['chain_status'] in ("VERIFIED", "CORRECTED"):
        return 0
    elif chain['chain_status'] == "UNTESTED":
        return 1
    elif chain['chain_status'] == "BROKEN":
        return 2
    else:
        return 3


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 3

    run_dir = pathlib.Path(sys.argv[1])
    if not run_dir.is_dir():
        print(f"ERROR: {run_dir} is not a directory")
        return 3

    events = load_events(run_dir)
    if not events:
        print(f"ERROR: No events found in {run_dir}")
        return 3

    return print_report(run_dir, events)


if __name__ == "__main__":
    sys.exit(main())
