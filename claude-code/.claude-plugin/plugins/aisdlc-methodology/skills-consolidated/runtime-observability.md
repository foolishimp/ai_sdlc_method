---
name: runtime-observability
description: Complete runtime observability workflow - telemetry tagging with REQ-* keys, deviation detection, production issue tracing, feedback loop closure. Consolidates create-observability-config, telemetry-tagging, trace-production-issue.
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob]
---

# Runtime Observability

**Skill Type**: Complete Workflow (Runtime Feedback Stage)
**Purpose**: Implement requirement-tagged telemetry and close the feedback loop
**Consolidates**: create-observability-config, telemetry-tagging, trace-production-issue

---

## When to Use This Skill

Use this skill when:
- Setting up observability for a new service
- Adding telemetry to existing code
- Tracing production issues back to requirements
- Closing the feedback loop from runtime to requirements
- Implementing homeostasis monitoring

---

## Observability Architecture

```
Runtime Metrics (REQ-* tagged)
    ↓
Telemetry Pipeline (Datadog/Prometheus/OTEL)
    ↓
Deviation Detection (actual vs. homeostasis target)
    ↓
Alert Generation (with REQ-* context)
    ↓
Feedback Loop (new intent generation)
    ↓
Requirements Stage (cycle repeats)
```

---

## Complete Workflow

### Phase 1: Create Observability Configuration

**Goal**: Set up telemetry infrastructure with REQ-* tagging.

**Configuration Template**:

```yaml
# config/observability.yml

# Observability Configuration
# Implements: REQ-RUNTIME-001 (Telemetry Tagging)

telemetry:
  provider: "opentelemetry"  # or datadog, prometheus
  service_name: "customer-portal"
  environment: "${ENV}"

  # Global tags applied to all metrics/traces
  global_tags:
    service: "customer-portal"
    version: "${VERSION}"
    environment: "${ENV}"

  # Metric definitions with REQ-* mapping
  metrics:
    - name: "login_attempts"
      type: "counter"
      description: "Number of login attempts"
      requirement: "REQ-F-AUTH-001"
      labels:
        - "status"      # success, failure
        - "reason"      # invalid_email, wrong_password, locked
        - "requirement" # REQ-* key

    - name: "login_latency_ms"
      type: "histogram"
      description: "Login response time in milliseconds"
      requirement: "REQ-NFR-PERF-001"
      constraint: "C-001"  # < 500ms
      buckets: [50, 100, 200, 500, 1000, 2000]
      labels:
        - "requirement"

    - name: "account_lockouts"
      type: "counter"
      description: "Number of account lockouts"
      requirement: "REQ-F-AUTH-001"
      business_rule: "BR-003"
      labels:
        - "requirement"
        - "business_rule"

  # Trace configuration
  traces:
    sample_rate: 0.1  # 10% sampling in production
    always_sample_errors: true
    propagation: ["tracecontext", "baggage"]

  # Homeostasis targets for deviation detection
  homeostasis:
    REQ-NFR-PERF-001:
      metric: "login_latency_ms"
      target: 500
      operator: "lt"  # less than
      alert_threshold: 0.95  # Alert if > 5% exceed target

    REQ-F-AUTH-001:
      metric: "login_success_rate"
      target: 0.99
      operator: "gte"  # greater than or equal
      alert_threshold: 0.98  # Alert if drops below 98%
```

---

### Phase 2: Implement Telemetry Tagging

**Goal**: Tag all metrics, logs, and traces with REQ-* keys.

**Python Implementation**:

```python
# observability/telemetry.py

# Implements: REQ-RUNTIME-001 (Telemetry Tagging)

import logging
import time
import functools
from typing import Optional, Dict, Any
from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode

# Initialize tracer and meter
tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

# Metrics with REQ-* tags
login_counter = meter.create_counter(
    name="login_attempts",
    description="Number of login attempts",
    unit="1"
)

login_latency = meter.create_histogram(
    name="login_latency_ms",
    description="Login response time",
    unit="ms"
)


def with_telemetry(
    requirement: str,
    business_rules: Optional[list] = None,
    constraints: Optional[list] = None
):
    """Decorator to add telemetry with REQ-* tagging.

    Implements: REQ-RUNTIME-001

    Args:
        requirement: REQ-* key this operation implements
        business_rules: List of BR-* keys
        constraints: List of C-* keys
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Build attributes
            attributes = {
                "requirement": requirement,
                "function": func.__name__,
            }
            if business_rules:
                attributes["business_rules"] = ",".join(business_rules)
            if constraints:
                attributes["constraints"] = ",".join(constraints)

            # Create span with REQ-* context
            with tracer.start_as_current_span(
                name=f"{requirement}:{func.__name__}",
                attributes=attributes
            ) as span:
                start_time = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
                finally:
                    # Record latency metric
                    elapsed_ms = (time.perf_counter() - start_time) * 1000
                    login_latency.record(elapsed_ms, attributes)

        return wrapper
    return decorator


class RequirementLogger:
    """Logger that automatically tags logs with REQ-* keys.

    Implements: REQ-RUNTIME-001
    """

    def __init__(self, logger: logging.Logger, requirement: str):
        self.logger = logger
        self.requirement = requirement

    def _log(self, level: int, msg: str, **kwargs):
        extra = kwargs.pop('extra', {})
        extra['requirement'] = self.requirement
        extra.update(kwargs)
        self.logger.log(level, msg, extra=extra)

    def info(self, msg: str, **kwargs):
        self._log(logging.INFO, msg, **kwargs)

    def warning(self, msg: str, **kwargs):
        self._log(logging.WARNING, msg, **kwargs)

    def error(self, msg: str, **kwargs):
        self._log(logging.ERROR, msg, **kwargs)


# Usage example
class AuthenticationService:
    """Authentication service with full telemetry.

    Implements: REQ-F-AUTH-001
    """

    def __init__(self):
        self.logger = RequirementLogger(
            logging.getLogger(__name__),
            "REQ-F-AUTH-001"
        )

    @with_telemetry(
        requirement="REQ-F-AUTH-001",
        business_rules=["BR-001", "BR-002", "BR-003"],
        constraints=["C-001"]
    )
    def login(self, email: str, password: str) -> LoginResult:
        """Authenticate user with telemetry.

        Implements: REQ-F-AUTH-001
        Business Rules: BR-001, BR-002, BR-003
        Constraints: C-001 (< 500ms)
        """
        # Record attempt
        login_counter.add(1, {
            "requirement": "REQ-F-AUTH-001",
            "status": "attempt"
        })

        # Validate email (BR-001)
        if not self.validate_email(email):
            login_counter.add(1, {
                "requirement": "REQ-F-AUTH-001",
                "status": "failure",
                "reason": "invalid_email",
                "business_rule": "BR-001"
            })
            self.logger.warning(
                "Login failed: invalid email",
                email=email,
                business_rule="BR-001"
            )
            return LoginResult(success=False, error="Invalid email")

        # ... rest of implementation

        # Record success
        login_counter.add(1, {
            "requirement": "REQ-F-AUTH-001",
            "status": "success"
        })
        self.logger.info("Login successful", user_id=user.id)
        return LoginResult(success=True, user=user)
```

---

### Phase 3: Deviation Detection

**Goal**: Compare runtime metrics against homeostasis targets.

**Implementation**:

```python
# observability/homeostasis.py

# Implements: REQ-RUNTIME-002 (Deviation Detection)

from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

@dataclass
class HomeostasisTarget:
    """Target state for a requirement.

    Implements: REQ-RUNTIME-002
    """
    requirement: str
    metric: str
    target: float
    operator: str  # lt, gt, lte, gte, eq
    alert_threshold: float
    description: str


@dataclass
class DeviationAlert:
    """Alert when runtime deviates from target.

    Implements: REQ-RUNTIME-002
    """
    requirement: str
    metric: str
    target: float
    actual: float
    deviation_percent: float
    severity: str  # warning, critical
    timestamp: datetime
    context: Dict[str, Any]


class HomeostasisMonitor:
    """Monitor runtime metrics against homeostasis targets.

    Implements: REQ-RUNTIME-002
    """

    def __init__(self, targets: Dict[str, HomeostasisTarget]):
        self.targets = targets
        self.alerts: list[DeviationAlert] = []

    def check_deviation(
        self,
        requirement: str,
        metric_value: float
    ) -> Optional[DeviationAlert]:
        """Check if metric deviates from homeostasis target.

        Implements: REQ-RUNTIME-002
        """
        target = self.targets.get(requirement)
        if not target:
            return None

        # Compare against target
        is_deviated = False
        if target.operator == "lt":
            is_deviated = metric_value >= target.target
        elif target.operator == "gt":
            is_deviated = metric_value <= target.target
        elif target.operator == "lte":
            is_deviated = metric_value > target.target
        elif target.operator == "gte":
            is_deviated = metric_value < target.target

        if not is_deviated:
            return None

        # Calculate deviation
        deviation = abs(metric_value - target.target) / target.target * 100

        alert = DeviationAlert(
            requirement=requirement,
            metric=target.metric,
            target=target.target,
            actual=metric_value,
            deviation_percent=deviation,
            severity="critical" if deviation > 20 else "warning",
            timestamp=datetime.utcnow(),
            context={
                "target_description": target.description,
                "operator": target.operator,
            }
        )

        self.alerts.append(alert)
        return alert


# Example usage
monitor = HomeostasisMonitor({
    "REQ-NFR-PERF-001": HomeostasisTarget(
        requirement="REQ-NFR-PERF-001",
        metric="login_latency_ms",
        target=500,
        operator="lt",
        alert_threshold=0.95,
        description="Login response time < 500ms"
    ),
    "REQ-F-AUTH-001": HomeostasisTarget(
        requirement="REQ-F-AUTH-001",
        metric="login_success_rate",
        target=0.99,
        operator="gte",
        alert_threshold=0.98,
        description="Login success rate >= 99%"
    )
})

# Check latency (called by monitoring system)
alert = monitor.check_deviation("REQ-NFR-PERF-001", 750)  # 750ms > 500ms
if alert:
    print(f"ALERT: {alert.requirement} - {alert.metric} at {alert.actual} "
          f"(target: {alert.target}, deviation: {alert.deviation_percent:.1f}%)")
```

---

### Phase 4: Trace Production Issues

**Goal**: Trace errors back to requirements for feedback loop.

**Implementation**:

```python
# observability/issue_tracer.py

# Implements: REQ-RUNTIME-003 (Feedback Loop Closure)

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class ProductionIssue:
    """Production issue with requirement traceability.

    Implements: REQ-RUNTIME-003
    """
    issue_id: str
    error_message: str
    stack_trace: str
    requirement: str
    business_rules: List[str]
    timestamp: datetime
    severity: str
    impact: str  # Number of users affected
    trace_id: str


@dataclass
class FeedbackIntent:
    """New intent generated from production issue.

    Implements: REQ-RUNTIME-003
    """
    intent_id: str
    source_issue: str
    requirement: str
    description: str
    priority: str
    created_at: datetime


class ProductionIssueTracer:
    """Trace production issues back to requirements.

    Implements: REQ-RUNTIME-003 (Feedback Loop Closure)
    """

    def trace_error(
        self,
        error: Exception,
        trace_context: dict
    ) -> ProductionIssue:
        """Extract requirement context from error.

        Implements: REQ-RUNTIME-003
        """
        # Extract REQ-* from span attributes or error context
        requirement = trace_context.get("requirement", "UNKNOWN")
        business_rules = trace_context.get("business_rules", "").split(",")

        issue = ProductionIssue(
            issue_id=f"ISSUE-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            requirement=requirement,
            business_rules=business_rules,
            timestamp=datetime.utcnow(),
            severity="critical" if "critical" in str(error).lower() else "high",
            impact=self._estimate_impact(trace_context),
            trace_id=trace_context.get("trace_id", "")
        )

        return issue

    def generate_feedback_intent(
        self,
        issue: ProductionIssue
    ) -> FeedbackIntent:
        """Generate new intent from production issue.

        Implements: REQ-RUNTIME-003 (Feedback Loop)

        This closes the loop:
        Runtime Issue → New Intent → Requirements → ... → Fixed Code
        """
        return FeedbackIntent(
            intent_id=f"INT-FB-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            source_issue=issue.issue_id,
            requirement=issue.requirement,
            description=f"Fix production issue: {issue.error_message}",
            priority="P0" if issue.severity == "critical" else "P1",
            created_at=datetime.utcnow()
        )
```

---

### Phase 5: Alert Configuration

**Goal**: Configure alerts with REQ-* context.

**Datadog Alert Example**:

```yaml
# alerts/login_latency_alert.yml

# Alert for: REQ-NFR-PERF-001 (Response Time)
# Constraint: C-001 (< 500ms)

name: "Login Latency Exceeds Target"
type: "metric alert"

query: |
  avg(last_5m):avg:login_latency_ms{
    requirement:REQ-NFR-PERF-001
  } > 500

message: |
  ## Login Latency Alert

  **Requirement**: REQ-NFR-PERF-001
  **Constraint**: C-001 (< 500ms)

  Current latency: {{value}}ms (target: 500ms)

  **Homeostasis Deviation**: Runtime metrics deviate from target state.

  **Action Required**:
  1. Check recent deployments
  2. Review database query performance
  3. Check external service latencies

  **Traceability**:
  - Requirement: REQ-NFR-PERF-001
  - Design: ADR-001 (Session Storage)
  - Code: src/auth/authentication.py

  @pagerduty-critical

tags:
  - "requirement:REQ-NFR-PERF-001"
  - "constraint:C-001"
  - "severity:critical"

priority: 1
notify_no_data: true
```

---

## Output Format

```
[RUNTIME OBSERVABILITY - REQ-F-AUTH-001]

Configuration Created:
  + config/observability.yml
  + alerts/login_latency_alert.yml
  + alerts/login_success_rate_alert.yml

Telemetry Implemented:
  + observability/telemetry.py
    - @with_telemetry decorator
    - RequirementLogger class
    - Metrics: login_attempts, login_latency_ms

Homeostasis Monitoring:
  + observability/homeostasis.py
    - REQ-NFR-PERF-001: latency < 500ms
    - REQ-F-AUTH-001: success rate >= 99%

Feedback Loop:
  + observability/issue_tracer.py
    - Trace errors to REQ-*
    - Generate feedback intents

Traceability:
  All metrics/logs/traces tagged with REQ-* keys

Runtime Observability Complete!
  Next: Deploy and monitor homeostasis
```

---

## Configuration

```yaml
# .claude/plugins.yml
plugins:
  - name: "@aisdlc/aisdlc-methodology"
    config:
      runtime:
        telemetry_provider: "opentelemetry"
        require_req_tags: true
        homeostasis_check_interval: "5m"
        alert_on_deviation: true
        auto_generate_intents: true
        feedback_loop_enabled: true
```

---

## Homeostasis Behavior

**If metric deviates from target**:
- Detect: actual > target (for latency)
- Signal: Alert with REQ-* context
- Action: Generate feedback intent
- Loop: New intent → Requirements → Fix

**If production error occurs**:
- Detect: Exception with REQ-* context
- Signal: Alert + trace to requirement
- Action: Generate feedback intent
- Loop: Fix deployed → Monitor → Verify homeostasis

---

## Key Principles Applied

- **Fail Fast**: Detect deviations immediately
- **No Legacy Baggage**: Clean up stale alerts
- **Perfectionist Excellence**: Full traceability end-to-end

**"Excellence or nothing"**
