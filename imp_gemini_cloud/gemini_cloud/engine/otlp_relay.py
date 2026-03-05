# Implements: ADR-GC-006, REQ-SENSE-006, ADR-S-014
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

class CloudOTLPRelay:
    """Tails local event logs and projects them into OTLP Spans.
    Optimized for multi-tenant Cloud environments.
    """
    
    def __init__(self, workspace_root: Path, collector_endpoint: str = "http://localhost:6006/v1/traces"):
        self.workspace_root = workspace_root
        self.log_path = workspace_root / "events" / "events.jsonl"
        self.collector_endpoint = collector_endpoint
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self._last_position = 0
        
        if OTLP_AVAILABLE:
            # Multi-tenant resource attributes
            resource = Resource.create({
                "service.name": "ai-sdlc-method-cloud",
                "project": "imp_gemini_cloud",
                "tenant.id": "default" # Can be dynamic
            })
            self.provider = TracerProvider(resource=resource)
            try:
                exporter = OTLPSpanExporter(endpoint=self.collector_endpoint)
                self.provider.add_span_processor(BatchSpanProcessor(exporter))
                self.tracer = trace.get_tracer(__name__, tracer_provider=self.provider)
            except Exception as e:
                print(f"  [OTLP-CLOUD] Failed to initialize exporter: {e}")
                self.tracer = None
        else:
            self.tracer = None

    def start(self):
        if not self.log_path.exists():
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            self.log_path.touch()
            
        self.running = True
        self._last_position = self.log_path.stat().st_size
        self.thread = threading.Thread(target=self._tail_loop, daemon=True)
        self.thread.start()
        print(f"  [OTLP-CLOUD] Relay started (watching: {self.log_path.name})")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)

    def _tail_loop(self):
        while self.running:
            self.process_events()
            time.sleep(1)

    def process_events(self):
        if not self.log_path.exists():
            return
            
        current_size = self.log_path.stat().st_size
        if current_size < self._last_position:
            self._last_position = 0
            
        if current_size > self._last_position:
            with open(self.log_path, "r") as f:
                f.seek(self._last_position)
                for line in f:
                    if line.strip():
                        try:
                            event = json.loads(line)
                            self._process_event(event)
                        except Exception as e:
                            print(f"  [OTLP-CLOUD] Error: {e}")
                self._last_position = f.tell()

    def _process_event(self, event: Dict):
        if not self.tracer:
            return

        facets = event.get("run", {}).get("facets", {})
        req_facet = facets.get("sdlc_req_keys", {})
        
        event_type = event.get("event_type") or "unknown"
        ol_type = event.get("eventType", "OTHER")
        feature_id = req_facet.get("feature_id", "unknown")
        edge_id = req_facet.get("edge", "unknown")
        
        # Determine archive path (Canonical Model)
        archive_path = ""
        project_root = self.workspace_root.parent
        runs_dir = project_root / "runs"
        if runs_dir.exists():
            safe_edge = edge_id.replace('→', '_').replace('↔', '_')
            match_pattern = f"run_{feature_id}_{safe_edge}_iter"
            matching_runs = sorted(list(runs_dir.glob(f"{match_pattern}*")), key=lambda x: x.stat().st_mtime, reverse=True)
            if matching_runs:
                archive_path = str(matching_runs[0])

        attributes = {
            "sdlc.event_type": event_type,
            "sdlc.feature_id": feature_id,
            "sdlc.edge_id": edge_id,
            "sdlc.lineage_path": f"{feature_id}:{edge_id}",
            "sdlc.run_archive_path": archive_path,
            "openlineage.run_id": event.get("run", {}).get("runId", ""),
            "project": "imp_gemini_cloud"
        }

        with self.tracer.start_as_current_span(f"{event_type}: {feature_id}", attributes=attributes) as span:
            if ol_type == "FAIL":
                span.set_status(trace.Status(trace.StatusCode.ERROR))
            elif ol_type == "COMPLETE":
                span.set_status(trace.Status(trace.StatusCode.OK))
            
            if "data" in event:
                span.add_event("data_payload", attributes={"json": json.dumps(event["data"])})
