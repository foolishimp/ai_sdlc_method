# Implements: ADR-S-014, REQ-SENSE-006
import json
import time
import threading
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, timezone

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    OTLP_AVAILABLE = True
except ImportError:
    OTLP_AVAILABLE = False

class OTLPRelay:
    """Tails events.jsonl and projects OpenLineage events into OTLP Spans.
    Follows mapping defined in ADR-S-014.
    """
    
    def __init__(self, workspace_root: Path, collector_endpoint: str = "http://localhost:6006/v1/traces"):
        self.workspace_root = workspace_root
        self.log_path = workspace_root / "events" / "events.jsonl"
        self.collector_endpoint = collector_endpoint
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self._last_position = 0
        
        if OTLP_AVAILABLE:
            from opentelemetry.sdk.resources import Resource
            resource = Resource.create({"service.name": "ai-sdlc-method", "project": "imp_gemini"})
            self.provider = TracerProvider(resource=resource)
            try:
                exporter = OTLPSpanExporter(endpoint=self.collector_endpoint)
                self.provider.add_span_processor(BatchSpanProcessor(exporter))
                self.tracer = trace.get_tracer(__name__, tracer_provider=self.provider)
            except Exception as e:
                print(f"  [OTLP] Failed to initialize exporter: {e}")
                self.tracer = None
        else:
            self.tracer = None

    def start(self):
        """Starts the tailing thread."""
        if not self.log_path.exists():
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            self.log_path.touch()
            
        self.running = True
        self._last_position = self.log_path.stat().st_size
        self.thread = threading.Thread(target=self._tail_loop, daemon=True)
        self.thread.start()
        print(f"  [OTLP] Relay started (watching: {self.log_path.name})")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)

    def _tail_loop(self):
        while self.running:
            self.process_events()
            time.sleep(1)

    def process_events(self):
        """Processes any new events in the log file since the last position."""
        if not self.log_path.exists():
            return
            
        current_size = self.log_path.stat().st_size
        if current_size < self._last_position:
            # Log rotated or truncated
            self._last_position = 0
            
        if current_size > self._last_position:
            with open(self.log_path, "r") as f:
                f.seek(self._last_position)
                for line in f:
                    if line.strip():
                        try:
                            event = json.loads(line)
                            self._process_event(event)
                            print(f"  [OTLP] Processed event: {event.get('run', {}).get('runId')}")
                        except Exception as e:
                            print(f"  [OTLP] Error processing event: {e}")
                self._last_position = f.tell()

    def _process_event(self, event: Dict):
        """Maps OpenLineage RunEvent to OTLP Span per ADR-S-014."""
        if not self.tracer:
            return

        # Extract facets
        facets = event.get("run", {}).get("facets", {})
        req_facet = facets.get("sdlc_req_keys", {})
        type_facet = facets.get("sdlc_event_type", {})
        
        event_type = event.get("event_type") or type_facet.get("type", "unknown")
        ol_type = event.get("eventType", "OTHER")
        feature_id = req_facet.get("feature_id", "unknown")
        edge_id = req_facet.get("edge", "unknown")
        regime = type_facet.get("regime", "unknown")
        
        # Mapping properties
        span_name = f"{event_type}: {feature_id}"
        
        # Lineage Path (Breadcrumb for easier navigation)
        lineage_path = f"{feature_id}:{edge_id}"
        
        # Determine archive path if available (Canonical Invocation Model)
        archive_path = ""
        project_root = self.workspace_root.parent
        runs_dir = project_root / "runs"
        if runs_dir.exists():
            # Find the most recent run for this feature/edge in events
            # (Heuristic: match by feature and edge name in dir name)
            safe_edge = edge_id.replace('→', '_').replace('↔', '_')
            match_pattern = f"run_{feature_id}_{safe_edge}_iter"
            matching_runs = sorted(list(runs_dir.glob(f"{match_pattern}*")), key=lambda x: x.stat().st_mtime, reverse=True)
            if matching_runs:
                archive_path = str(matching_runs[0])

        attributes = {
            "sdlc.event_type": event_type,
            "sdlc.feature_id": feature_id,
            "sdlc.edge_id": edge_id,
            "sdlc.regime": regime,
            "sdlc.lineage_path": lineage_path,
            "sdlc.run_archive_path": archive_path,
            "sdlc.req_keys": req_facet.get("req_keys", []),
            "sdlc.correlation_id": event.get("run", {}).get("runId", ""), # Run ID is the correlation for this thread
            "openlineage.run_id": event.get("run", {}).get("runId", ""),
            "openlineage.job_name": event.get("job", {}).get("name", ""),
            "project": event.get("project", "unknown")
        }

        # Handle causal propagation (as defined in ADR-S-014)
        parent_facet = facets.get("parent_run_id", {})
        parent_id = parent_facet.get("runId")
        if parent_id:
            attributes["sdlc.causation_id"] = parent_id
            attributes["sdlc.parent_run_id"] = parent_id

        # We "simulate" the span lifecycle from the discrete events
        # Note: In a real OTLP stream, we'd start a span on START 
        # and end it on COMPLETE. Since we are tailing a log of discrete events,
        # we emit a single "Event Span" or a "Completion Span".
        
        with self.tracer.start_as_current_span(span_name, attributes=attributes) as span:
            if ol_type == "FAIL":
                span.set_status(trace.Status(trace.StatusCode.ERROR))
            elif ol_type == "COMPLETE":
                span.set_status(trace.Status(trace.StatusCode.OK))
            
            # Add event-specific data as span events
            if "data" in event:
                span.add_event("data_payload", attributes={"json": json.dumps(event["data"])})
