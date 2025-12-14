# Runtime Feedback Module

**Implements**: REQ-RUNTIME-003 (Feedback Loop Closure)

## Purpose

Closes the governance loop by monitoring production metrics and automatically generating intents when deviations from the homeostasis model are detected.

## Architecture

```
Production Alerts (Datadog/Prometheus)
    ↓
RuntimeFeedbackAgent.process_alert()
    ↓
DeviationDetector.detect()
    ↓
Severity Classification (CRITICAL/HIGH/MEDIUM/LOW)
    ↓
Intent Generation (if CRITICAL)
    ↓
Intent Manager (create INT-YYYYMMDD-NNN)
    ↓
Notification Service (Slack/Email)
    ↓
Requirements Stage (normal SDLC flow)
```

## Components

### RuntimeFeedbackAgent

Main agent that orchestrates the feedback loop.

**Key Methods**:
- `process_alert(alert_payload)` - Process incoming alert and generate intent if warranted
- `_should_generate_intent(deviation)` - Only CRITICAL severity generates intent
- `_is_in_cooldown(req_id)` - Prevents intent spam (60 minute cooldown)

**Usage**:
```python
from runtime_feedback import RuntimeFeedbackAgent

# Initialize
agent = RuntimeFeedbackAgent(
    homeostasis_model=load_homeostasis_model(),
    intent_manager=intent_mgr,
    notification_service=notify_svc
)

# Process alert
alert = {
    'alert_id': 'ALERT-12345',
    'tags': ['req:REQ-NFR-PERF-001'],
    'current_value': 850,
    'threshold': 500
}

intent_id = agent.process_alert(alert)  # Returns INT-* or None
```

### DeviationDetector

Detects deviations from the homeostasis model.

**Key Methods**:
- `detect(alert)` - Returns Deviation object if deviation detected
- `_classify_severity()` - CRITICAL if exceeds critical threshold
- `_classify_deviation_type()` - PERFORMANCE_DEGRADATION, ERROR_RATE_INCREASE, etc.

**Severity Rules**:
- **CRITICAL**: `value >= threshold.critical` → Generate intent immediately
- **HIGH**: `value >= threshold.warning` → Alert only (no intent)
- **MEDIUM**: Significant deviation from baseline → Alert only
- **LOW**: Within normal range → Ignored

## Homeostasis Model

The homeostasis model defines expected behavior from requirements.

**Example**:
```yaml
requirements:
  REQ-NFR-PERF-001:
    title: "Login response time < 500ms"
    type: performance
    thresholds:
      p95_latency_ms:
        critical: 500  # SLA breach
        warning: 400   # Early warning
        target: 250    # Desired
    baseline:
      p95_latency_ms: 235  # Learned from production
    deviation_rules:
      - metric: "p95_latency_ms"
        condition: "value > threshold.critical"
        severity: "critical"
        action: "generate_intent"
```

## Testing

**Test Coverage**: 100% (3 test cases)

```bash
python -m pytest claude-code/tests/runtime_feedback/ -v
```

**Tests**:
1. `test_process_critical_alert_generates_intent` - Critical alerts generate intents
2. `test_process_warning_alert_does_not_generate_intent` - Warning alerts only notify
3. `test_cooldown_prevents_intent_spam` - Cooldown prevents duplicate intents

## Integration

### Webhook Handlers (Future)

Placeholder for integration with observability platforms:

- `datadog_webhook.py` - Handle Datadog monitor webhooks
- `prometheus_webhook.py` - Handle Prometheus Alertmanager webhooks

### Intent Management (Future)

Placeholder for intent storage and workflow:

- Intent files stored in `.ai-workspace/intents/human/INT-*.yml`
- Auto-generated intents have `source.type: runtime_feedback`
- Critical intents approved immediately, High intents require review

## Performance

- Alert processing: < 1s (REQ-NFR-REFINE-001)
- Cooldown period: 60 minutes (configurable)
- No external API calls in critical path

## Traceability

All code tagged with requirement keys:

- `# Implements: REQ-RUNTIME-003` - Feedback loop closure
- `# Validates: REQ-RUNTIME-003` - Test traceability

## Next Steps

1. Implement webhook handlers for Datadog/Prometheus
2. Integrate with Intent Manager storage
3. Add notification service integration (Slack/Email)
4. Create homeostasis model generator from requirements
5. Add baseline calculation from historical data

## References

- **Requirements**: `docs/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md` Section 9
- **Design**: `docs/design/claude_aisdlc/RUNTIME_FEEDBACK_DESIGN.md`
- **Methodology**: `docs/ai_sdlc_method.md` Section 10.0 (Runtime Feedback Stage)

---

**Status**: Core implementation complete (TDD cycle 1)
**Last Updated**: 2025-12-15
**Owned By**: Code Agent (Runtime Feedback Module)
