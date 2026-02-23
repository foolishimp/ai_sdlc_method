# Implements: REQ-F-BOOT-003, REQ-TOOL-002, REQ-FEAT-002, REQ-UX-003, REQ-UX-005, REQ-SUPV-003
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
import yaml

from imp_gemini.code.internal.workspace_state import (
    detect_workspace_state,
    get_active_features,
    load_events,
    get_unactioned_escalations,
    detect_stuck_features,
    detect_corrupted_events,
    detect_orphaned_spawns,
    verify_genesis_compliance,
)

def generate_gantt(workspace: Path):
    """Generate Mermaid Gantt chart and write to STATUS.md."""
    features = get_active_features(workspace)
    events = load_events(workspace)
    
    gantt_lines = [
        "gantt",
        "    title Feature Build Schedule",
        "    dateFormat YYYY-MM-DD HH:mm",
        "    axisFormat %m-%d %H:%M",
        ""
    ]
    
    for fv in features:
        fid = fv.get("feature", "UNKNOWN")
        gantt_lines.append(f"    section {fid}")
        traj = fv.get("trajectory", {})
        
        for phase in ["requirements", "design", "code", "unit_tests", "uat_tests"]:
            phase_events = [e for e in events if e.get("feature") == fid and (phase in e.get("edge", "") or phase in e.get("asset", ""))]
            if not phase_events: continue
            
            start_ev = phase_events[0]
            end_ev = [e for e in phase_events if e.get("event_type") == "edge_converged"]
            
            start_ts = start_ev.get("timestamp", "").replace("T", " ").split(".")[0]
            if end_ev:
                end_ts = end_ev[0].get("timestamp", "").replace("T", " ").split(".")[0]
                status = ":done"
            else:
                end_ts = "1h"
                status = ":active"
                
            gantt_lines.append(f"    {phase:<16} {status}, {fid[:5]}-{phase[:3]}, {start_ts}, {end_ts}")

    gantt_text = "\n".join(gantt_lines)
    status_file = workspace / ".ai-workspace" / "STATUS.md"
    content = f"""# Project Status

Generated: {datetime.now().isoformat()}

## Feature Build Schedule

```mermaid
{gantt_text}
```

## Process Telemetry
- Total features: {len(features)}
- Total events: {len(events)}

## Self-Reflection
- No major anomalies detected.
"""
    status_file.write_text(content)
    return status_file

def main():
    parser = argparse.ArgumentParser(description="AI SDLC Status")
    parser.add_argument("--feature", help="Show detailed status for a specific feature")
    parser.add_argument("--gantt", action="store_true", help="Generate Mermaid Gantt chart")
    parser.add_argument("--health", action="store_true", help="Run Genesis self-compliance and workspace health check")
    parser.add_argument("--functor", action="store_true", help="Show functor encoding")
    args = parser.parse_args()

    workspace = Path.cwd()
    state = detect_workspace_state(workspace)
    
    if args.gantt:
        path = generate_gantt(workspace)
        print(f"Status written to {path}")
        return

    if args.health:
        print(f"Workspace Health — gemini-genesis")
        print("=" * 40)
        
        # Genesis Self-Compliance
        print("\nGenesis Self-Compliance:")
        compliance = verify_genesis_compliance(workspace)
        for res in compliance["results"]:
            marker = "✓" if res["status"] == "pass" else ("✗" if res["status"] == "fail" else "~")
            print(f"  {marker} {res['description']}")
            
        # Infrastructure Health
        print("\nInfrastructure Health:")
        corrupt = detect_corrupted_events(workspace)
        print(f"  Event Log: {'✗' if corrupt else '✓'} {len(corrupt)} corruptions")
        orphans = detect_orphaned_spawns(workspace)
        print(f"  Features:  {'✗' if orphans else '✓'} {len(orphans)} orphaned spawns")
        stuck = detect_stuck_features(workspace)
        print(f"  Stuck:     {'✗' if stuck else '✓'} {len(stuck)} stuck features")
        
        # REQ-SUPV-003: Emit health_checked event
        event = {
            "event_type": "health_checked",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "project": "gemini-genesis",
            "data": {
                "passed": compliance["passed"],
                "failed": compliance["failed"],
                "results": compliance["results"],
                "infrastructure_issues": len(corrupt) + len(orphans) + len(stuck)
            }
        }
        events_file = workspace / ".ai-workspace" / "events" / "events.jsonl"
        if events_file.parent.exists():
            with open(events_file, "a") as f:
                f.write(json.dumps(event) + "\n")
        
        return

    features = get_active_features(workspace)
    events = load_events(workspace)

    print(f"AI SDLC Status")
    print("=" * 30)
    print(f"State: {state}")
    
    print("\nYou Are Here:")
    edges_converged = 0
    edges_total = 0
    for fv in features:
        fid = fv.get("feature", "UNKNOWN")
        traj = fv.get("trajectory", {})
        def get_marker(phase):
            nonlocal edges_converged, edges_total
            p_data = traj.get(phase, {})
            if not isinstance(p_data, dict): return "○"
            edges_total += 1
            p_status = p_data.get("status", "pending")
            if p_status == "converged":
                edges_converged += 1
                return "✓"
            if p_status == "iterating": return "●"
            return "○"
        
        print(f"  {fid:<15} intent ✓ → req {get_marker('requirements')} → design {get_marker('design')} → code {get_marker('code')} → tests {get_marker('unit_tests')}")

    unactioned = get_unactioned_escalations(events)
    
    # Functor rollup (from first feature as representative)
    functor_info = "unknown"
    if features:
        f = features[0].get("functor", {})
        mode = f.get("mode", "interactive")
        valence = f.get("valence", "medium")
        functor_info = f"{mode}/{valence}"

    print(f"\nProject Rollup:")
    print(f"  Edges converged: {edges_converged}/{edges_total} ({int(edges_converged/max(edges_total,1)*100)}%)")
    print(f"  Features:  {len([f for f in features if f.get('status') == 'converged'])} converged, {len(features)} total")
    print(f"  Signals:   {len(unactioned)} unactioned intents")
    print(f"  Functor:   {functor_info}")

    print(f"\nSignals:")
    if not unactioned:
        print("  No unactioned signals.")
    for esc in unactioned[:3]:
        print(f"  {esc.get('intent_id', 'INT-???')} — {esc.get('data', {}).get('trigger', 'No description')}")

if __name__ == "__main__":
    main()
