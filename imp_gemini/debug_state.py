from pathlib import Path
from gemini_cli.engine.state import EventStore, Projector

events = EventStore(Path(".ai-workspace")).load_all()
events = sorted(events, key=lambda x: x.get("timestamp") or x.get("eventTime") or "")

for ev in events:
    facets = ev.get("run", {}).get("facets", {})
    req_facet = facets.get("sdlc_req_keys", {})
    payload = facets.get("sdlc:payload", {})
    type_facet = facets.get("sdlc_event_type", {})
    
    e_type = type_facet.get("type") or ev.get("event_type")
    feat = req_facet.get("feature_id") or payload.get("feature") or ev.get("feature") or facets.get("sdlc:universal", {}).get("instance_id")
    edge_name = req_facet.get("edge") or payload.get("edge") or ev.get("edge")
    
    if feat == "REQ-F-ADR-LINK-001" and edge_name in ("design→test_cases", "design->test_cases"):
        print(f"Time: {ev.get('eventTime') or ev.get('timestamp')}, Type: {e_type}, Feat: {feat}, Edge: {edge_name}")
        if e_type in ("iteration_completed", "IterationCompleted"):
            data = ev.get("data") or ev.get("_metadata", {}).get("original_data", {})
            delta_facet = facets.get("sdlc_delta", {})
            
            delta = data.get("delta")
            if delta is None: delta = payload.get("delta")
            if delta is None: delta = delta_facet.get("value")
            if delta is None: delta = -1
            
            converged_val = payload.get("converged")
            if converged_val is None: converged_val = delta_facet.get("converged")
            if converged_val is None: converged_val = (delta == 0)
            
            print(f"  -> delta: {delta}, converged_val: {converged_val}")

status = Projector.get_feature_status(events)
print("FINAL STATUS:", status["REQ-F-ADR-LINK-001"]["trajectory"]["design→test_cases"])
