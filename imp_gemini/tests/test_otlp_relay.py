import pytest
import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch
from gemini_cli.engine.otlp_relay import OTLPRelay

def test_otlp_relay_mapping(tmp_path):
    """Verifies OpenLineage to OTLP mapping per ADR-S-014."""
    # Setup
    workspace_root = tmp_path / ".ai-workspace"
    workspace_root.mkdir()
    log_path = workspace_root / "events" / "events.jsonl"
    log_path.parent.mkdir()
    
    # Mock OpenTelemetry
    with patch("gemini_cli.engine.otlp_relay.trace") as mock_trace:
        mock_tracer = MagicMock()
        mock_trace.get_tracer.return_value = mock_tracer
        
        # Instantiate Relay
        relay = OTLPRelay(workspace_root)
        relay.tracer = mock_tracer # Force mock tracer
        
        # Create a sample OpenLineage event
        event = {
            "eventType": "START",
            "run": {
                "runId": "test-run-123",
                "facets": {
                    "sdlc_req_keys": {
                        "feature_id": "REQ-F-AUTH-001",
                        "edge": "design->code",
                        "req_keys": ["REQ-AUTH-001", "REQ-AUTH-002"]
                    },
                    "sdlc_event_type": {"type": "edge_started"}
                }
            },
            "job": {"name": "REQ-F-AUTH-001:design->code"},
            "project": "test-project"
        }
        
        # Write event to log
        with open(log_path, "w") as f:
            f.write(json.dumps(event) + "\n")
            
        # Test the _process_event directly for mapping
        relay._process_event(event)
        
        # Verify Mapping
        mock_tracer.start_as_current_span.assert_called()
        args, kwargs = mock_tracer.start_as_current_span.call_args
        
        span_name = args[0]
        attributes = kwargs.get("attributes", {})
        
        assert span_name == "edge_started: REQ-F-AUTH-001"
        assert attributes["sdlc.event_type"] == "edge_started"
        assert attributes["sdlc.feature_id"] == "REQ-F-AUTH-001"
        assert attributes["sdlc.edge_id"] == "design->code"
        assert attributes["sdlc.req_keys"] == ["REQ-AUTH-001", "REQ-AUTH-002"]
        assert attributes["openlineage.run_id"] == "test-run-123"
        assert attributes["project"] == "test-project"

def test_otlp_relay_completion_status(tmp_path):
    """Verifies OTLP span status mapping for COMPLETE events."""
    workspace_root = tmp_path / ".ai-workspace"
    workspace_root.mkdir()
    log_path = workspace_root / "events" / "events.jsonl"
    log_path.parent.mkdir()
    
    with patch("gemini_cli.engine.otlp_relay.trace") as mock_trace:
        from opentelemetry import trace as otel_trace
        # Only mock the tracer, keep Status/StatusCode real
        mock_trace.StatusCode = otel_trace.StatusCode
        mock_trace.Status = otel_trace.Status
        
        mock_tracer = MagicMock()
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span
        mock_trace.get_tracer.return_value = mock_tracer
        
        relay = OTLPRelay(workspace_root)
        relay.tracer = mock_tracer
        
        # Complete event
        event = {
            "eventType": "COMPLETE",
            "run": {"facets": {"sdlc_event_type": {"type": "edge_converged"}}}
        }
        
        relay._process_event(event)
        
        # Verify span status was set to OK
        mock_span.set_status.assert_called()
        status = mock_span.set_status.call_args[0][0]
        assert status.status_code == otel_trace.StatusCode.OK
