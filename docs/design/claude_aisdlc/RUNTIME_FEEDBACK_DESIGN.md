# Runtime Feedback System - Design Document

**Document Type**: Technical Design Specification
**Project**: ai_sdlc_method (claude_aisdlc solution)
**Version**: 1.0
**Date**: 2025-12-03
**Status**: Draft
**Stage**: Design (Section 5.0)

---

## Requirements Traceability

This design implements the following requirements:

| Requirement | Description | Priority | Maps To |
|-------------|-------------|----------|---------|
| REQ-RUNTIME-001 | Telemetry Tagging | High | Sections 2, 3 |
| REQ-RUNTIME-002 | Deviation Detection | High | Sections 4, 5 |
| REQ-RUNTIME-003 | Feedback Loop Closure | Critical | Sections 6, 7 |

**Source**: [AISDLC_IMPLEMENTATION_REQUIREMENTS.md](../../requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md) Section 9

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Telemetry Tagging System](#2-telemetry-tagging-system)
3. [Telemetry Formats](#3-telemetry-formats)
4. [Homeostasis Model](#4-homeostasis-model)
5. [Deviation Detection Engine](#5-deviation-detection-engine)
6. [Feedback Loop Workflow](#6-feedback-loop-workflow)
7. [Integration Architecture](#7-integration-architecture)
8. [Storage Design](#8-storage-design)
9. [Implementation Guidance](#9-implementation-guidance)
10. [Examples](#10-examples)

---

## 1. Executive Summary

### 1.1 Purpose

The Runtime Feedback System **closes the governance loop** by monitoring production systems and automatically generating intents when deviations from expected behavior are detected. This creates a **homeostatic system** that self-corrects toward the desired state.

### 1.2 Design Principles

1. **Requirement Tagging** - All telemetry tagged with REQ-* keys
2. **Homeostasis Model** - Define expected behavior from requirements
3. **Automatic Detection** - No manual monitoring required
4. **Traceable Feedback** - Deviations → Intents → Requirements → Fix
5. **Configurable Thresholds** - Different sensitivity per requirement
6. **Non-Intrusive** - Works with existing observability platforms

### 1.3 Key Design Decisions

| Decision | Rationale | Requirement |
|----------|-----------|-------------|
| Structured logging format | Machine-parsable, REQ tags extractable | REQ-RUNTIME-001 |
| Tag-based metrics | Platform-agnostic, works with Datadog/Prometheus | REQ-RUNTIME-001 |
| Threshold-based detection | Simple, predictable, well-understood | REQ-RUNTIME-002 |
| Severity classification | Prioritize critical deviations | REQ-RUNTIME-002 |
| Auto-intent generation | Fast response, reduces manual effort | REQ-RUNTIME-003 |
| Human review gate | Prevents alert fatigue | REQ-RUNTIME-003 |

### 1.4 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Production Environment                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│  │Application │→ │Logs        │→ │Metrics     │                │
│  │(REQ tags)  │  │(REQ tags)  │  │(REQ tags)  │                │
│  └────────────┘  └────────────┘  └────────────┘                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Observability Platform (Datadog/Prometheus)         │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ Alert: "REQ-NFR-PERF-001 threshold exceeded"           │     │
│  │ P95 latency: 850ms (threshold: 500ms)                 │     │
│  └────────────────────────────────────────────────────────┘     │
└────────────────────────────┬────────────────────────────────────┘
                             │ (webhook)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Runtime Feedback Agent                              │
│  1. Receive alert                                               │
│  2. Extract REQ-* tags                                          │
│  3. Query homeostasis model for thresholds                      │
│  4. Classify deviation severity                                 │
│  5. Generate intent (if warranted)                              │
│  6. Notify stakeholders                                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Intent Management                             │
│  File: .ai-workspace/intents/human/INT-20251203-042.yml        │
│  Type: remediate                                               │
│  Source: runtime_feedback                                      │
│  Status: draft (awaits review)                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Human Review & Approval                      │
│  On-call engineer reviews auto-generated intent                │
│  Approves → Flows to Requirements stage                        │
│  Rejects → Intent archived with reason                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Telemetry Tagging System

### 2.1 Tagging Philosophy

**Implements**: REQ-RUNTIME-001

Every log entry, metric, and alert must be **tagged with the requirement key(s) it implements**. This enables:

- **Requirement-level observability** - Query all telemetry for REQ-NFR-PERF-001
- **Impact analysis** - Know which requirements are affected by an incident
- **Root cause tracing** - Alert → REQ → Code → Design → Requirement → Intent
- **Homeostasis monitoring** - Compare observed vs. expected behavior per requirement

### 2.2 Tagging Patterns

#### 2.2.1 Code-Level Tags

**Pattern**: Tag functions/classes with `# Implements: REQ-*` comments

```python
# src/auth/login.py

# Implements: REQ-F-AUTH-001, REQ-NFR-PERF-001
def login(email: str, password: str) -> LoginResult:
    """
    User login with email and password.

    Performance SLA: < 500ms (REQ-NFR-PERF-001)
    """
    start_time = time.time()

    try:
        # Validate credentials
        user = authenticate(email, password)

        # Log success with requirement tag
        logger.info(
            "Login successful",
            extra={
                "req": "REQ-F-AUTH-001",
                "user_id": user.id,
                "latency_ms": (time.time() - start_time) * 1000
            }
        )

        # Emit metric with requirement tag
        metrics.histogram(
            "auth.login.latency",
            (time.time() - start_time) * 1000,
            tags=["req:REQ-NFR-PERF-001"]
        )

        return LoginResult(success=True, user=user)

    except AuthenticationError as e:
        logger.error(
            "Login failed",
            extra={
                "req": "REQ-F-AUTH-001",
                "error": str(e),
                "latency_ms": (time.time() - start_time) * 1000
            }
        )

        metrics.increment(
            "auth.login.errors",
            tags=["req:REQ-F-AUTH-001", "error_type:auth_failed"]
        )

        raise
```

#### 2.2.2 Log Entry Tags

**Format**: Structured logging with `req` field

```json
{
  "timestamp": "2025-12-03T14:32:15.123Z",
  "level": "INFO",
  "message": "Login successful",
  "req": "REQ-F-AUTH-001",
  "user_id": "user-12345",
  "latency_ms": 120,
  "service": "auth-service",
  "environment": "production"
}
```

#### 2.2.3 Metric Tags

**Datadog format**:
```python
statsd.histogram(
    "auth.login.latency",
    120,  # milliseconds
    tags=["req:REQ-NFR-PERF-001", "env:production", "service:auth"]
)

statsd.increment(
    "auth.login.success",
    tags=["req:REQ-F-AUTH-001", "env:production"]
)
```

**Prometheus format**:
```python
auth_login_latency_seconds{req="REQ-NFR-PERF-001", env="production"} 0.120
auth_login_total{req="REQ-F-AUTH-001", status="success", env="production"} 1
```

#### 2.2.4 Alert Tags

**Alert payload** (Datadog webhook):
```json
{
  "alert_id": "12345",
  "title": "High latency on auth.login",
  "message": "P95 latency exceeded threshold for REQ-NFR-PERF-001",
  "severity": "critical",
  "tags": ["req:REQ-NFR-PERF-001", "service:auth"],
  "query": "avg(last_5m):p95:auth.login.latency{req:REQ-NFR-PERF-001} > 500",
  "current_value": 850,
  "threshold": 500,
  "timestamp": "2025-12-03T14:32:15Z"
}
```

### 2.3 Tag Extraction Algorithm

**Purpose**: Extract REQ-* tags from telemetry data

```python
import re
from typing import List

REQ_TAG_PATTERN = re.compile(r'REQ-(F|NFR|DATA|BR)-[A-Z]{2,10}-\d{3}')

def extract_req_tags(data: dict | str) -> List[str]:
    """
    Extract requirement tags from telemetry data.

    Args:
        data: Dictionary (log entry, alert payload) or string

    Returns:
        List of unique REQ-* tags found

    Examples:
        >>> extract_req_tags({"req": "REQ-F-AUTH-001", "message": "Login"})
        ['REQ-F-AUTH-001']

        >>> extract_req_tags("REQ-NFR-PERF-001 threshold exceeded")
        ['REQ-NFR-PERF-001']
    """
    if isinstance(data, dict):
        # Check common tag fields
        tag_fields = ['req', 'requirement', 'tags']
        for field in tag_fields:
            if field in data:
                value = data[field]
                if isinstance(value, str):
                    tags = REQ_TAG_PATTERN.findall(value)
                    if tags:
                        return [f"REQ-{tag}" for tag in tags]
                elif isinstance(value, list):
                    # Extract from tag list
                    all_tags = []
                    for tag in value:
                        found = REQ_TAG_PATTERN.findall(str(tag))
                        all_tags.extend([f"REQ-{t}" for t in found])
                    return list(set(all_tags))

        # Recursively search all string values
        all_tags = []
        for value in data.values():
            if isinstance(value, str):
                tags = REQ_TAG_PATTERN.findall(value)
                all_tags.extend([f"REQ-{tag}" for tag in tags])
        return list(set(all_tags))

    elif isinstance(data, str):
        tags = REQ_TAG_PATTERN.findall(data)
        return [f"REQ-{tag}" for tag in tags]

    return []
```

---

## 3. Telemetry Formats

### 3.1 Structured Logging Format

**Purpose**: Standardized log format with requirement tags

#### 3.1.1 Python (JSON logging)

```python
# logging_config.py

import logging
import json
from datetime import datetime

class RequirementTagFormatter(logging.Formatter):
    """Custom formatter that ensures REQ tags are present"""

    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "service": "auth-service",  # From config
            "environment": "production",  # From config
        }

        # Add requirement tag if present
        if hasattr(record, 'req'):
            log_data['req'] = record.req
        elif hasattr(record, 'requirement'):
            log_data['req'] = record.requirement

        # Add extra fields
        if hasattr(record, 'extra'):
            log_data.update(record.extra)

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data)

# Configure logger
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(RequirementTagFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Usage
logger.info(
    "Login successful",
    extra={
        "req": "REQ-F-AUTH-001",
        "user_id": "user-12345",
        "latency_ms": 120
    }
)
```

#### 3.1.2 JavaScript/TypeScript (Winston)

```typescript
// logger.ts

import winston from 'winston';

const requirementFormat = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DDTHH:mm:ss.SSSZ' }),
  winston.format.json()
);

const logger = winston.createLogger({
  level: 'info',
  format: requirementFormat,
  defaultMeta: {
    service: 'auth-service',
    environment: process.env.NODE_ENV || 'development'
  },
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'app.log' })
  ]
});

// Usage
logger.info('Login successful', {
  req: 'REQ-F-AUTH-001',
  user_id: 'user-12345',
  latency_ms: 120
});
```

### 3.2 Metrics Format

#### 3.2.1 Datadog (StatsD)

```python
# metrics.py

from datadog import statsd
from typing import List

class RequirementMetrics:
    """Wrapper for metrics with requirement tagging"""

    def __init__(self, service_name: str, environment: str):
        self.base_tags = [
            f"service:{service_name}",
            f"env:{environment}"
        ]

    def histogram(self, metric_name: str, value: float, req: str, extra_tags: List[str] = None):
        """Record histogram metric with requirement tag"""
        tags = self.base_tags + [f"req:{req}"]
        if extra_tags:
            tags.extend(extra_tags)

        statsd.histogram(metric_name, value, tags=tags)

    def increment(self, metric_name: str, req: str, extra_tags: List[str] = None):
        """Increment counter metric with requirement tag"""
        tags = self.base_tags + [f"req:{req}"]
        if extra_tags:
            tags.extend(extra_tags)

        statsd.increment(metric_name, tags=tags)

    def gauge(self, metric_name: str, value: float, req: str, extra_tags: List[str] = None):
        """Set gauge metric with requirement tag"""
        tags = self.base_tags + [f"req:{req}"]
        if extra_tags:
            tags.extend(extra_tags)

        statsd.gauge(metric_name, value, tags=tags)

# Usage
metrics = RequirementMetrics("auth-service", "production")

metrics.histogram(
    "auth.login.latency",
    120,  # milliseconds
    req="REQ-NFR-PERF-001"
)

metrics.increment(
    "auth.login.success",
    req="REQ-F-AUTH-001"
)
```

#### 3.2.2 Prometheus

```python
# prometheus_metrics.py

from prometheus_client import Counter, Histogram, Gauge

# Define metrics with requirement label
auth_login_latency = Histogram(
    'auth_login_latency_seconds',
    'Login latency in seconds',
    ['req', 'service', 'environment']
)

auth_login_total = Counter(
    'auth_login_total',
    'Total login attempts',
    ['req', 'status', 'service', 'environment']
)

auth_active_sessions = Gauge(
    'auth_active_sessions',
    'Number of active sessions',
    ['req', 'service', 'environment']
)

# Usage
auth_login_latency.labels(
    req='REQ-NFR-PERF-001',
    service='auth-service',
    environment='production'
).observe(0.120)

auth_login_total.labels(
    req='REQ-F-AUTH-001',
    status='success',
    service='auth-service',
    environment='production'
).inc()
```

### 3.3 Alert Format

#### 3.3.1 Datadog Monitor Configuration

```yaml
# datadog_monitors.yml

- name: "REQ-NFR-PERF-001: Login latency threshold"
  type: metric alert
  query: "avg(last_5m):p95:auth.login.latency{req:REQ-NFR-PERF-001,env:production} > 500"
  message: |
    ## Login Latency Threshold Exceeded

    **Requirement**: REQ-NFR-PERF-001
    **Threshold**: 500ms (P95)
    **Current Value**: {{value}}ms
    **Duration**: {{last_triggered_at}}

    This alert indicates that the login latency SLA has been violated.

    **Actions**:
    1. Check auth-service health
    2. Review recent deployments
    3. Check database connection pool
    4. Escalate to on-call if sustained > 15 minutes

    **Runbook**: https://wiki.company.com/runbooks/auth-latency
    **Dashboard**: https://app.datadoghq.com/dashboard/auth-service

  tags:
    - req:REQ-NFR-PERF-001
    - service:auth
    - sla:critical

  priority: P2
  notify:
    - "@oncall-backend"
    - "@slack-alerts-backend"

- name: "REQ-F-AUTH-001: High error rate"
  type: metric alert
  query: "avg(last_5m):sum:auth.login.errors{req:REQ-F-AUTH-001,env:production}.as_rate() > 0.05"
  message: |
    ## Login Error Rate Elevated

    **Requirement**: REQ-F-AUTH-001
    **Threshold**: 5% error rate
    **Current Value**: {{value}}%

    Login errors are above acceptable threshold.

  tags:
    - req:REQ-F-AUTH-001
    - service:auth

  priority: P3
  notify:
    - "@oncall-backend"
```

#### 3.3.2 Prometheus Alertmanager

```yaml
# prometheus_alerts.yml

groups:
  - name: auth_requirements
    interval: 30s
    rules:
      - alert: REQ_NFR_PERF_001_Violated
        expr: |
          histogram_quantile(0.95,
            rate(auth_login_latency_seconds_bucket{req="REQ-NFR-PERF-001"}[5m])
          ) > 0.5
        for: 5m
        labels:
          severity: critical
          req: REQ-NFR-PERF-001
          service: auth
        annotations:
          summary: "Login latency SLA violated"
          description: |
            P95 latency for REQ-NFR-PERF-001 is {{ $value }}s (threshold: 0.5s)

            This indicates a violation of the login performance SLA.

            Runbook: https://wiki.company.com/runbooks/auth-latency

      - alert: REQ_F_AUTH_001_ErrorRate
        expr: |
          rate(auth_login_total{req="REQ-F-AUTH-001",status="error"}[5m]) /
          rate(auth_login_total{req="REQ-F-AUTH-001"}[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
          req: REQ-F-AUTH-001
          service: auth
        annotations:
          summary: "Login error rate elevated"
          description: "Error rate for REQ-F-AUTH-001 is {{ $value | humanizePercentage }}"
```

---

## 4. Homeostasis Model

### 4.1 Concept

**Implements**: REQ-RUNTIME-002

The **homeostasis model** defines the **expected behavior** of each requirement. It consists of:

1. **Thresholds** - Acceptable ranges for metrics (from REQ-NFR-*)
2. **Baseline** - Normal operating values
3. **Tolerance** - Acceptable deviation from baseline
4. **Severity Levels** - How far from expected triggers what response

### 4.2 Homeostasis Schema

```yaml
# File: .ai-workspace/observability/homeostasis_model.yml

homeostasis_model:
  version: "1.0"
  generated_at: "2025-12-03T14:00:00Z"

  requirements:
    REQ-NFR-PERF-001:
      title: "Login response time < 500ms"
      type: performance

      # Thresholds (from requirement definition)
      thresholds:
        p50_latency_ms:
          target: 120
          warning: 300
          critical: 500
          unit: "milliseconds"

        p95_latency_ms:
          target: 250
          warning: 400
          critical: 500
          unit: "milliseconds"

        p99_latency_ms:
          target: 400
          warning: 500
          critical: 800
          unit: "milliseconds"

      # Baseline (learned from production data)
      baseline:
        p50_latency_ms: 115
        p95_latency_ms: 235
        p99_latency_ms: 380
        sample_period: "30 days"
        last_updated: "2025-12-01T00:00:00Z"

      # Deviation detection
      deviation_rules:
        - metric: "p95_latency_ms"
          condition: "value > threshold.critical"
          severity: "critical"
          action: "generate_intent"
          cooldown: "1 hour"  # Don't spam intents

        - metric: "p95_latency_ms"
          condition: "value > threshold.warning"
          severity: "warning"
          action: "alert_only"

        - metric: "p50_latency_ms"
          condition: "value > baseline * 2"
          severity: "warning"
          action: "alert_only"

      # Telemetry mapping
      telemetry:
        datadog:
          metric: "auth.login.latency"
          tags: ["req:REQ-NFR-PERF-001"]
          aggregation: "p95"

        prometheus:
          metric: "auth_login_latency_seconds"
          labels: {"req": "REQ-NFR-PERF-001"}
          quantile: 0.95

    REQ-F-AUTH-001:
      title: "User login functionality"
      type: functional

      thresholds:
        error_rate:
          target: 0.001  # 0.1%
          warning: 0.01   # 1%
          critical: 0.05  # 5%
          unit: "ratio"

        success_rate:
          target: 0.999   # 99.9%
          warning: 0.99   # 99%
          critical: 0.95  # 95%
          unit: "ratio"

      baseline:
        error_rate: 0.0008
        success_rate: 0.9992
        sample_period: "30 days"
        last_updated: "2025-12-01T00:00:00Z"

      deviation_rules:
        - metric: "error_rate"
          condition: "value > threshold.critical"
          severity: "critical"
          action: "generate_intent"
          cooldown: "30 minutes"

        - metric: "success_rate"
          condition: "value < threshold.critical"
          severity: "critical"
          action: "generate_intent"
          cooldown: "30 minutes"

      telemetry:
        datadog:
          metric: "auth.login.errors"
          tags: ["req:REQ-F-AUTH-001"]
          aggregation: "rate"

    REQ-NFR-AVAIL-001:
      title: "Service availability 99.9%"
      type: availability

      thresholds:
        uptime_percentage:
          target: 99.99
          warning: 99.9
          critical: 99.0
          unit: "percent"

        max_downtime_minutes_per_month:
          target: 4.3   # 99.99%
          warning: 43.2  # 99.9%
          critical: 432  # 99%
          unit: "minutes"

      deviation_rules:
        - metric: "uptime_percentage"
          condition: "value < threshold.critical"
          severity: "critical"
          action: "generate_intent_immediate"  # No cooldown

        - metric: "uptime_percentage"
          condition: "value < threshold.warning"
          severity: "warning"
          action: "alert_only"
```

### 4.3 Threshold Definition from Requirements

**Process**: Extract thresholds from NFR requirements

```python
# homeostasis_extractor.py

import re
from typing import Dict, Any

def extract_thresholds_from_requirement(req_doc: str) -> Dict[str, Any]:
    """
    Extract thresholds from requirement document.

    Args:
        req_doc: Markdown requirement document content

    Returns:
        Dictionary of thresholds and constraints

    Example:
        Input: "Login response time shall be less than 500ms (P95)"
        Output: {
            "metric": "latency_ms",
            "percentile": 95,
            "threshold": 500,
            "operator": "<"
        }
    """
    thresholds = {}

    # Pattern: "< 500ms"
    latency_pattern = r'<\s*(\d+)\s*ms\s*\(P(\d+)\)'
    match = re.search(latency_pattern, req_doc)
    if match:
        threshold_ms = int(match.group(1))
        percentile = int(match.group(2))
        thresholds[f'p{percentile}_latency_ms'] = {
            'critical': threshold_ms,
            'warning': int(threshold_ms * 0.8),  # 80% of critical
            'target': int(threshold_ms * 0.5),   # 50% of critical
            'unit': 'milliseconds'
        }

    # Pattern: "99.9% uptime"
    uptime_pattern = r'(\d+\.?\d*)%\s+uptime'
    match = re.search(uptime_pattern, req_doc)
    if match:
        uptime_pct = float(match.group(1))
        thresholds['uptime_percentage'] = {
            'critical': uptime_pct,
            'warning': uptime_pct + 0.09,  # Slightly better
            'target': uptime_pct + 0.1,
            'unit': 'percent'
        }

    # Pattern: "error rate < 1%"
    error_rate_pattern = r'error\s+rate\s*<\s*(\d+\.?\d*)%'
    match = re.search(error_rate_pattern, req_doc, re.IGNORECASE)
    if match:
        error_rate_pct = float(match.group(1))
        thresholds['error_rate'] = {
            'critical': error_rate_pct / 100,  # Convert to ratio
            'warning': (error_rate_pct / 100) * 0.5,
            'target': (error_rate_pct / 100) * 0.1,
            'unit': 'ratio'
        }

    return thresholds
```

### 4.4 Baseline Calculation

**Purpose**: Learn normal operating behavior from production data

```python
# baseline_calculator.py

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List

class BaselineCalculator:
    """Calculate baseline metrics from historical data"""

    def calculate_baseline(
        self,
        metric_name: str,
        historical_data: List[float],
        sample_period_days: int = 30
    ) -> Dict[str, float]:
        """
        Calculate baseline from historical data.

        Args:
            metric_name: Name of metric
            historical_data: List of metric values over sample period
            sample_period_days: Number of days of data

        Returns:
            Baseline statistics
        """
        data = np.array(historical_data)

        return {
            'mean': float(np.mean(data)),
            'median': float(np.median(data)),
            'p50': float(np.percentile(data, 50)),
            'p95': float(np.percentile(data, 95)),
            'p99': float(np.percentile(data, 99)),
            'stddev': float(np.std(data)),
            'min': float(np.min(data)),
            'max': float(np.max(data)),
            'sample_size': len(data),
            'sample_period_days': sample_period_days,
            'last_updated': datetime.now().isoformat()
        }

    def detect_anomaly(
        self,
        current_value: float,
        baseline: Dict[str, float],
        threshold_sigmas: float = 3.0
    ) -> bool:
        """
        Detect if current value is anomalous compared to baseline.

        Uses z-score: (value - mean) / stddev

        Args:
            current_value: Current metric value
            baseline: Baseline statistics
            threshold_sigmas: Number of standard deviations for anomaly

        Returns:
            True if anomalous
        """
        mean = baseline['mean']
        stddev = baseline['stddev']

        z_score = abs((current_value - mean) / stddev) if stddev > 0 else 0

        return z_score > threshold_sigmas
```

---

## 5. Deviation Detection Engine

### 5.1 Detection Algorithm

**Implements**: REQ-RUNTIME-002

```python
# deviation_detector.py

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class DeviationType(Enum):
    PERFORMANCE_DEGRADATION = "performance_degradation"
    ERROR_RATE_INCREASE = "error_rate_increase"
    SLA_BREACH = "sla_breach"
    AVAILABILITY_LOSS = "availability_loss"

class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class Deviation:
    """Represents a detected deviation from expected behavior"""
    req_id: str
    deviation_type: DeviationType
    severity: Severity
    metric_name: str
    current_value: float
    threshold_value: float
    baseline_value: float
    deviation_percentage: float
    detected_at: str
    telemetry_links: List[str]
    context: dict

class DeviationDetector:
    """Detects deviations from homeostasis model"""

    def __init__(self, homeostasis_model: dict):
        self.model = homeostasis_model

    def detect(self, alert: dict) -> Optional[Deviation]:
        """
        Detect deviation from alert payload.

        Args:
            alert: Alert payload from observability platform

        Returns:
            Deviation object if deviation detected, None otherwise
        """
        # Extract REQ tags
        req_tags = extract_req_tags(alert)
        if not req_tags:
            return None

        req_id = req_tags[0]  # Primary requirement

        # Get homeostasis model for this requirement
        if req_id not in self.model['requirements']:
            return None

        req_model = self.model['requirements'][req_id]

        # Extract metric info from alert
        current_value = alert.get('current_value')
        metric_name = self._extract_metric_name(alert)

        if not current_value or not metric_name:
            return None

        # Get threshold and baseline
        thresholds = req_model['thresholds'].get(metric_name, {})
        baseline = req_model['baseline'].get(metric_name, 0)

        # Determine severity
        severity = self._classify_severity(
            current_value,
            thresholds,
            baseline
        )

        if severity == Severity.LOW:
            return None  # Not significant enough

        # Determine deviation type
        deviation_type = self._classify_deviation_type(
            req_model['type'],
            metric_name,
            current_value,
            thresholds
        )

        # Calculate deviation percentage
        if baseline > 0:
            deviation_pct = ((current_value - baseline) / baseline) * 100
        else:
            deviation_pct = 100.0

        return Deviation(
            req_id=req_id,
            deviation_type=deviation_type,
            severity=severity,
            metric_name=metric_name,
            current_value=current_value,
            threshold_value=thresholds.get('critical', 0),
            baseline_value=baseline,
            deviation_percentage=deviation_pct,
            detected_at=alert.get('timestamp'),
            telemetry_links=self._extract_telemetry_links(alert),
            context={
                'alert_id': alert.get('alert_id'),
                'service': alert.get('service'),
                'environment': alert.get('environment')
            }
        )

    def _classify_severity(
        self,
        value: float,
        thresholds: dict,
        baseline: float
    ) -> Severity:
        """Classify deviation severity"""
        if not thresholds:
            return Severity.LOW

        critical = thresholds.get('critical')
        warning = thresholds.get('warning')

        if critical and value >= critical:
            return Severity.CRITICAL
        elif warning and value >= warning:
            return Severity.HIGH
        elif baseline > 0 and abs(value - baseline) / baseline > 0.5:
            return Severity.MEDIUM
        else:
            return Severity.LOW

    def _classify_deviation_type(
        self,
        req_type: str,
        metric_name: str,
        value: float,
        thresholds: dict
    ) -> DeviationType:
        """Classify type of deviation"""
        if req_type == "performance" or "latency" in metric_name:
            return DeviationType.PERFORMANCE_DEGRADATION
        elif "error" in metric_name or "failure" in metric_name:
            return DeviationType.ERROR_RATE_INCREASE
        elif "uptime" in metric_name or "availability" in metric_name:
            return DeviationType.AVAILABILITY_LOSS
        else:
            return DeviationType.SLA_BREACH

    def _extract_metric_name(self, alert: dict) -> Optional[str]:
        """Extract metric name from alert query"""
        query = alert.get('query', '')
        # Parse Datadog query: "avg(last_5m):p95:auth.login.latency{...} > 500"
        # Extract "p95" or metric name

        # Simple heuristic: look for common patterns
        if 'p95' in query.lower():
            return 'p95_latency_ms'
        elif 'p99' in query.lower():
            return 'p99_latency_ms'
        elif 'error' in query.lower():
            return 'error_rate'
        elif 'uptime' in query.lower():
            return 'uptime_percentage'

        return None

    def _extract_telemetry_links(self, alert: dict) -> List[str]:
        """Extract telemetry dashboard links from alert"""
        links = []

        # Datadog dashboard link
        if 'dashboard_url' in alert:
            links.append(alert['dashboard_url'])

        # Sentry issue link
        if 'sentry_url' in alert:
            links.append(alert['sentry_url'])

        return links
```

### 5.2 Severity Classification Rules

```yaml
# File: .ai-workspace/observability/severity_rules.yml

severity_rules:
  critical:
    conditions:
      - "value >= threshold.critical"
      - "duration > 5 minutes"
    actions:
      - generate_intent_immediate
      - notify_oncall
      - create_incident
    response_sla: "15 minutes"

  high:
    conditions:
      - "value >= threshold.warning"
      - "value < threshold.critical"
      - "duration > 10 minutes"
    actions:
      - generate_intent_after_review
      - notify_team
    response_sla: "1 hour"

  medium:
    conditions:
      - "deviation > 50% from baseline"
      - "value < threshold.warning"
    actions:
      - alert_only
      - log_to_deviation_history
    response_sla: "4 hours"

  low:
    conditions:
      - "deviation <= 50% from baseline"
      - "value < threshold.warning"
    actions:
      - log_only
    response_sla: "none"
```

### 5.3 Alert Generation Rules

```python
# alert_generator.py

from typing import Optional

class AlertGenerator:
    """Generate alerts for deviations"""

    def generate_alert(self, deviation: Deviation) -> Optional[dict]:
        """
        Generate alert payload for deviation.

        Args:
            deviation: Detected deviation

        Returns:
            Alert payload for notification system
        """
        if deviation.severity in [Severity.CRITICAL, Severity.HIGH]:
            return {
                'alert_type': 'deviation_detected',
                'req_id': deviation.req_id,
                'severity': deviation.severity.value,
                'title': f"{deviation.req_id}: {deviation.deviation_type.value}",
                'message': self._format_message(deviation),
                'actions': self._determine_actions(deviation),
                'notify': self._determine_recipients(deviation),
                'telemetry_links': deviation.telemetry_links,
                'detected_at': deviation.detected_at
            }

        return None

    def _format_message(self, deviation: Deviation) -> str:
        """Format alert message"""
        return f"""
## Deviation Detected: {deviation.req_id}

**Type**: {deviation.deviation_type.value.replace('_', ' ').title()}
**Severity**: {deviation.severity.value.upper()}

**Metric**: {deviation.metric_name}
**Current Value**: {deviation.current_value:.2f}
**Threshold**: {deviation.threshold_value:.2f}
**Baseline**: {deviation.baseline_value:.2f}
**Deviation**: {deviation.deviation_percentage:+.1f}%

**Detected**: {deviation.detected_at}

**Context**:
- Service: {deviation.context.get('service', 'unknown')}
- Environment: {deviation.context.get('environment', 'unknown')}
- Alert ID: {deviation.context.get('alert_id', 'N/A')}

**Telemetry**: {', '.join(deviation.telemetry_links)}

**Next Steps**:
1. Review telemetry dashboards
2. Check recent deployments
3. Investigate root cause
4. Approve auto-generated intent (if created)
        """.strip()

    def _determine_actions(self, deviation: Deviation) -> list:
        """Determine required actions based on severity"""
        if deviation.severity == Severity.CRITICAL:
            return [
                'generate_intent_immediate',
                'create_incident',
                'notify_oncall'
            ]
        elif deviation.severity == Severity.HIGH:
            return [
                'generate_intent_after_review',
                'notify_team'
            ]
        else:
            return ['alert_only']

    def _determine_recipients(self, deviation: Deviation) -> list:
        """Determine who to notify"""
        if deviation.severity == Severity.CRITICAL:
            return ['@oncall', '@slack-incidents']
        elif deviation.severity == Severity.HIGH:
            return ['@team-backend', '@slack-alerts']
        else:
            return ['@slack-monitoring']
```

---

## 6. Feedback Loop Workflow

### 6.1 Feedback Loop States

**Implements**: REQ-RUNTIME-003

```
Deviation Detected → Severity Classification → Intent Generation → Human Review → SDLC Flow
```

### 6.2 Complete Feedback Loop

```python
# runtime_feedback_agent.py

from typing import Optional
from datetime import datetime

class RuntimeFeedbackAgent:
    """Agent that closes the feedback loop from production to requirements"""

    def __init__(
        self,
        homeostasis_model: dict,
        intent_manager: 'IntentManager',
        notification_service: 'NotificationService'
    ):
        self.detector = DeviationDetector(homeostasis_model)
        self.alert_generator = AlertGenerator()
        self.intent_manager = intent_manager
        self.notification_service = notification_service
        self.cooldown_tracker = {}  # Track recent intents to prevent spam

    def process_alert(self, alert_payload: dict) -> Optional[str]:
        """
        Process alert and potentially generate intent.

        Args:
            alert_payload: Alert from observability platform

        Returns:
            Intent ID if generated, None otherwise
        """
        # Step 1: Detect deviation
        deviation = self.detector.detect(alert_payload)

        if not deviation:
            return None

        # Step 2: Generate alert
        alert = self.alert_generator.generate_alert(deviation)

        if not alert:
            return None

        # Step 3: Check if intent generation is warranted
        should_generate = self._should_generate_intent(deviation)

        if not should_generate:
            # Just alert, don't generate intent
            self.notification_service.send(alert)
            return None

        # Step 4: Check cooldown (prevent intent spam)
        if self._is_in_cooldown(deviation.req_id):
            return None

        # Step 5: Generate intent
        intent_id = self._generate_intent(deviation, alert_payload)

        # Step 6: Track cooldown
        self._record_intent_generation(deviation.req_id)

        # Step 7: Notify stakeholders
        self.notification_service.send_with_intent(alert, intent_id)

        return intent_id

    def _should_generate_intent(self, deviation: Deviation) -> bool:
        """Determine if deviation warrants intent generation"""
        # Critical severity always generates intent
        if deviation.severity == Severity.CRITICAL:
            return True

        # High severity generates intent after human review
        if deviation.severity == Severity.HIGH:
            return True  # Will be marked as draft for review

        # Medium/Low only alert
        return False

    def _is_in_cooldown(self, req_id: str, cooldown_minutes: int = 60) -> bool:
        """Check if we recently generated intent for this requirement"""
        if req_id not in self.cooldown_tracker:
            return False

        last_generated = self.cooldown_tracker[req_id]
        elapsed = (datetime.now() - last_generated).total_seconds() / 60

        return elapsed < cooldown_minutes

    def _record_intent_generation(self, req_id: str):
        """Record that we generated an intent"""
        self.cooldown_tracker[req_id] = datetime.now()

    def _generate_intent(self, deviation: Deviation, alert_payload: dict) -> str:
        """Generate intent from deviation"""
        # Build intent data
        intent_data = {
            'classification': {
                'work_type': 'remediate',
                'category': 'bug' if deviation.deviation_type == DeviationType.ERROR_RATE_INCREASE else 'performance',
                'priority': 'critical' if deviation.severity == Severity.CRITICAL else 'high',
                'impact': 'high'
            },
            'title': f"[RUNTIME] {deviation.req_id}: {deviation.deviation_type.value.replace('_', ' ').title()}",
            'description': self._format_intent_description(deviation, alert_payload),
            'source': {
                'type': 'runtime_feedback',
                'author': 'runtime-feedback-agent',
                'timestamp': datetime.now().isoformat(),
                'context': f"Alert: {alert_payload.get('alert_id', 'N/A')}"
            },
            'incident': {
                'severity': deviation.severity.value,
                'detected_at': deviation.detected_at,
                'affected_requirements': [deviation.req_id],
                'telemetry_links': deviation.telemetry_links,
                'deviation_details': {
                    'metric': deviation.metric_name,
                    'current_value': deviation.current_value,
                    'threshold': deviation.threshold_value,
                    'baseline': deviation.baseline_value,
                    'deviation_pct': deviation.deviation_percentage
                }
            },
            'status': 'draft' if deviation.severity == Severity.HIGH else 'approved'
        }

        # Create intent via Intent Manager
        intent_id = self.intent_manager.create_intent(intent_data)

        return intent_id

    def _format_intent_description(self, deviation: Deviation, alert: dict) -> str:
        """Format intent description"""
        return f"""
🚨 AUTOMATICALLY GENERATED FROM RUNTIME FEEDBACK

## Deviation Summary

A {deviation.severity.value} deviation has been detected in production.

**Requirement**: {deviation.req_id}
**Deviation Type**: {deviation.deviation_type.value.replace('_', ' ').title()}
**Severity**: {deviation.severity.value.upper()}
**Detected**: {deviation.detected_at}

## Metrics

**Metric**: {deviation.metric_name}
**Current Value**: {deviation.current_value:.2f}
**Threshold**: {deviation.threshold_value:.2f} (SLA limit)
**Baseline**: {deviation.baseline_value:.2f} (normal)
**Deviation**: {deviation.deviation_percentage:+.1f}% from baseline

## Context

**Service**: {deviation.context.get('service', 'unknown')}
**Environment**: {deviation.context.get('environment', 'unknown')}
**Alert ID**: {deviation.context.get('alert_id', 'N/A')}

## Telemetry

{chr(10).join(f'- {link}' for link in deviation.telemetry_links)}

## Root Cause Analysis

**Status**: Investigation needed

**Recommended Actions**:
1. Review recent deployments
2. Check service health metrics
3. Analyze error logs for {deviation.req_id}
4. Compare with historical baselines
5. Identify root cause
6. Implement fix
7. Deploy and validate

## Acceptance Criteria

- [ ] Root cause identified and documented
- [ ] Fix implemented and tested
- [ ] Metric returns to baseline values
- [ ] Deployment successful
- [ ] No regression in related requirements
- [ ] Postmortem document created (if critical)
- [ ] Monitoring/alerts updated to prevent recurrence

## Related Requirements

This deviation traces back to:
- {deviation.req_id} (primary)

Review the requirement definition to understand the original intent and acceptance criteria.
        """.strip()
```

### 6.3 Intent Approval Workflow

```python
# intent_approval.py

from enum import Enum

class ApprovalDecision(Enum):
    APPROVE = "approve"
    REJECT = "reject"
    MODIFY = "modify"

class IntentApprovalWorkflow:
    """Workflow for reviewing auto-generated intents"""

    def review_intent(
        self,
        intent_id: str,
        reviewer: str,
        decision: ApprovalDecision,
        comments: str = ""
    ) -> bool:
        """
        Review and approve/reject auto-generated intent.

        Args:
            intent_id: Intent ID to review
            reviewer: Email of reviewer
            decision: Approval decision
            comments: Optional review comments

        Returns:
            True if intent workflow should proceed
        """
        intent = self.intent_manager.get_intent(intent_id)

        if decision == ApprovalDecision.APPROVE:
            # Approve intent, flows to Requirements stage
            intent['status'] = 'approved'
            intent['status_history'].append({
                'status': 'approved',
                'timestamp': datetime.now().isoformat(),
                'author': reviewer,
                'comment': comments or 'Approved runtime feedback intent'
            })
            self.intent_manager.update_intent(intent)

            # Notify Requirements Agent
            self.notification_service.notify_requirements_agent(intent_id)

            return True

        elif decision == ApprovalDecision.REJECT:
            # Reject intent, archive with reason
            intent['status'] = 'rejected'
            intent['status_history'].append({
                'status': 'rejected',
                'timestamp': datetime.now().isoformat(),
                'author': reviewer,
                'comment': comments or 'Rejected - not warranted'
            })
            self.intent_manager.update_intent(intent)

            return False

        elif decision == ApprovalDecision.MODIFY:
            # Keep as draft, human will edit before approval
            intent['status_history'].append({
                'status': 'modified',
                'timestamp': datetime.now().isoformat(),
                'author': reviewer,
                'comment': comments
            })
            self.intent_manager.update_intent(intent)

            return False
```

---

## 7. Integration Architecture

### 7.1 Observability Platform Integration

#### 7.1.1 Datadog Webhook Handler

```python
# datadog_webhook.py

from flask import Flask, request, jsonify
from typing import Dict

app = Flask(__name__)

class DatadogWebhookHandler:
    """Handle webhooks from Datadog"""

    def __init__(self, runtime_feedback_agent: RuntimeFeedbackAgent):
        self.agent = runtime_feedback_agent

    @app.route('/webhooks/datadog', methods=['POST'])
    def handle_webhook(self):
        """
        Handle Datadog monitor alert webhook.

        Payload format:
        {
          "alert_id": "12345",
          "title": "High latency on auth.login",
          "body": "...",
          "tags": ["req:REQ-NFR-PERF-001", ...],
          "metric": "auth.login.latency",
          "current_value": 850,
          "threshold": 500,
          "timestamp": "2025-12-03T14:32:15Z"
        }
        """
        payload = request.json

        # Normalize to standard format
        alert = self._normalize_datadog_alert(payload)

        # Process via Runtime Feedback Agent
        intent_id = self.agent.process_alert(alert)

        if intent_id:
            return jsonify({
                'status': 'intent_generated',
                'intent_id': intent_id
            }), 201
        else:
            return jsonify({
                'status': 'alert_processed_no_intent'
            }), 200

    def _normalize_datadog_alert(self, payload: Dict) -> Dict:
        """Normalize Datadog payload to standard format"""
        return {
            'alert_id': payload.get('id'),
            'title': payload.get('title'),
            'message': payload.get('body'),
            'tags': payload.get('tags', []),
            'query': payload.get('query', ''),
            'current_value': payload.get('last_triggered_at_epoch'),
            'threshold': self._extract_threshold_from_query(payload.get('query', '')),
            'timestamp': payload.get('date'),
            'service': self._extract_tag_value(payload.get('tags', []), 'service'),
            'environment': self._extract_tag_value(payload.get('tags', []), 'env'),
            'dashboard_url': f"https://app.datadoghq.com/monitors/{payload.get('id')}"
        }

    def _extract_threshold_from_query(self, query: str) -> float:
        """Extract threshold value from Datadog query"""
        import re
        match = re.search(r'>\s*(\d+)', query)
        return float(match.group(1)) if match else 0

    def _extract_tag_value(self, tags: list, key: str) -> str:
        """Extract value from tag list"""
        for tag in tags:
            if tag.startswith(f"{key}:"):
                return tag.split(':', 1)[1]
        return 'unknown'
```

#### 7.1.2 Prometheus Alertmanager Integration

```python
# prometheus_webhook.py

from flask import Flask, request, jsonify

app = Flask(__name__)

class PrometheusWebhookHandler:
    """Handle webhooks from Prometheus Alertmanager"""

    def __init__(self, runtime_feedback_agent: RuntimeFeedbackAgent):
        self.agent = runtime_feedback_agent

    @app.route('/webhooks/prometheus', methods=['POST'])
    def handle_webhook(self):
        """
        Handle Alertmanager webhook.

        Payload format:
        {
          "alerts": [
            {
              "status": "firing",
              "labels": {
                "alertname": "REQ_NFR_PERF_001_Violated",
                "severity": "critical",
                "req": "REQ-NFR-PERF-001",
                "service": "auth"
              },
              "annotations": {
                "summary": "Login latency SLA violated",
                "description": "P95 latency is 0.85s (threshold: 0.5s)"
              },
              "startsAt": "2025-12-03T14:32:15Z",
              "generatorURL": "..."
            }
          ]
        }
        """
        payload = request.json

        intent_ids = []

        for alert_data in payload.get('alerts', []):
            # Only process firing alerts
            if alert_data['status'] != 'firing':
                continue

            # Normalize to standard format
            alert = self._normalize_prometheus_alert(alert_data)

            # Process via Runtime Feedback Agent
            intent_id = self.agent.process_alert(alert)

            if intent_id:
                intent_ids.append(intent_id)

        if intent_ids:
            return jsonify({
                'status': 'intents_generated',
                'intent_ids': intent_ids
            }), 201
        else:
            return jsonify({
                'status': 'alerts_processed_no_intents'
            }), 200

    def _normalize_prometheus_alert(self, alert_data: dict) -> dict:
        """Normalize Prometheus payload to standard format"""
        labels = alert_data.get('labels', {})
        annotations = alert_data.get('annotations', {})

        # Extract current value and threshold from description
        # Example: "P95 latency is 0.85s (threshold: 0.5s)"
        description = annotations.get('description', '')
        current_value, threshold = self._parse_description(description)

        return {
            'alert_id': f"{labels.get('alertname')}_{alert_data.get('startsAt')}",
            'title': annotations.get('summary', ''),
            'message': description,
            'tags': [f"{k}:{v}" for k, v in labels.items()],
            'query': '',  # Not available in Alertmanager payload
            'current_value': current_value,
            'threshold': threshold,
            'timestamp': alert_data.get('startsAt'),
            'service': labels.get('service', 'unknown'),
            'environment': labels.get('environment', 'production'),
            'dashboard_url': alert_data.get('generatorURL', '')
        }

    def _parse_description(self, description: str) -> tuple:
        """Parse current value and threshold from description"""
        import re

        # Match "is X (threshold: Y)"
        match = re.search(r'is\s+([\d.]+)\w*\s+\(threshold:\s+([\d.]+)', description)

        if match:
            current = float(match.group(1))
            threshold = float(match.group(2))
            return current, threshold

        return 0, 0
```

### 7.2 Notification Integration

```python
# notification_service.py

import requests
from typing import Dict

class NotificationService:
    """Send notifications to various channels"""

    def __init__(self, config: dict):
        self.slack_webhook_url = config.get('slack_webhook_url')
        self.email_config = config.get('email')

    def send(self, alert: dict):
        """Send alert notification"""
        # Send to Slack
        if self.slack_webhook_url:
            self._send_slack(alert)

        # Send email
        if alert.get('notify'):
            self._send_email(alert)

    def send_with_intent(self, alert: dict, intent_id: str):
        """Send notification with intent link"""
        alert['intent_id'] = intent_id
        alert['intent_url'] = f"file://.ai-workspace/intents/human/{intent_id}.yml"

        self.send(alert)

    def _send_slack(self, alert: dict):
        """Send Slack notification"""
        severity_emoji = {
            'critical': ':rotating_light:',
            'high': ':warning:',
            'medium': ':information_source:',
            'low': ':white_check_mark:'
        }

        emoji = severity_emoji.get(alert['severity'], ':question:')

        message = {
            'text': f"{emoji} *{alert['title']}*",
            'blocks': [
                {
                    'type': 'header',
                    'text': {
                        'type': 'plain_text',
                        'text': f"{emoji} {alert['title']}"
                    }
                },
                {
                    'type': 'section',
                    'text': {
                        'type': 'mrkdwn',
                        'text': alert['message']
                    }
                },
                {
                    'type': 'section',
                    'fields': [
                        {
                            'type': 'mrkdwn',
                            'text': f"*Requirement:*\n{alert['req_id']}"
                        },
                        {
                            'type': 'mrkdwn',
                            'text': f"*Severity:*\n{alert['severity'].upper()}"
                        }
                    ]
                }
            ]
        }

        if 'intent_id' in alert:
            message['blocks'].append({
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': f":memo: *Auto-generated Intent:* `{alert['intent_id']}`"
                }
            })

        if alert.get('telemetry_links'):
            message['blocks'].append({
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': '*Telemetry:*\n' + '\n'.join(f"• <{link}|Dashboard>" for link in alert['telemetry_links'])
                }
            })

        requests.post(self.slack_webhook_url, json=message)

    def _send_email(self, alert: dict):
        """Send email notification"""
        # Implement email sending via SMTP or service
        pass
```

---

## 8. Storage Design

### 8.1 Deviation History

```yaml
# File: .ai-workspace/observability/deviation_history/{req_id}_HISTORY.yml

deviation_history:
  req_id: REQ-NFR-PERF-001
  title: "Login response time < 500ms"

  deviations:
    - deviation_id: "DEV-20251203-001"
      detected_at: "2025-12-03T14:32:15Z"
      resolved_at: "2025-12-03T15:45:00Z"
      severity: critical
      deviation_type: performance_degradation

      metrics:
        p95_latency_ms:
          current: 850
          threshold: 500
          baseline: 235
          deviation_pct: 261.7

      intent_generated: INT-20251203-042
      resolution:
        root_cause: "Database connection pool exhaustion"
        fix: "Released connections before external API calls"
        deployed_at: "2025-12-03T15:30:00Z"
        verified_at: "2025-12-03T15:45:00Z"

    - deviation_id: "DEV-20251201-008"
      detected_at: "2025-12-01T09:15:00Z"
      resolved_at: "2025-12-01T09:45:00Z"
      severity: high
      deviation_type: performance_degradation

      metrics:
        p95_latency_ms:
          current: 450
          threshold: 500
          baseline: 240
          deviation_pct: 87.5

      intent_generated: null  # Resolved before intent needed
      resolution:
        root_cause: "Spike in traffic during marketing campaign"
        fix: "Auto-scaled, no code change needed"
        deployed_at: null
        verified_at: "2025-12-01T09:45:00Z"
```

### 8.2 Feedback Loop Audit Trail

```yaml
# File: .ai-workspace/observability/feedback_audit.yml

feedback_audit:
  - event_id: "FB-20251203-001"
    timestamp: "2025-12-03T14:32:15Z"
    event_type: "deviation_detected"
    req_id: "REQ-NFR-PERF-001"
    deviation_id: "DEV-20251203-001"
    severity: "critical"
    action: "intent_generated"
    intent_id: "INT-20251203-042"

  - event_id: "FB-20251203-002"
    timestamp: "2025-12-03T14:35:00Z"
    event_type: "intent_approved"
    intent_id: "INT-20251203-042"
    approved_by: "john.doe@company.com"
    comment: "Legitimate performance issue, proceeding with fix"

  - event_id: "FB-20251203-003"
    timestamp: "2025-12-03T15:00:00Z"
    event_type: "requirements_stage_started"
    intent_id: "INT-20251203-042"
    agent: "AISDLC Requirements Agent"

  - event_id: "FB-20251203-004"
    timestamp: "2025-12-03T15:30:00Z"
    event_type: "fix_deployed"
    intent_id: "INT-20251203-042"
    deployment_version: "v2.3.2"

  - event_id: "FB-20251203-005"
    timestamp: "2025-12-03T15:45:00Z"
    event_type: "deviation_resolved"
    deviation_id: "DEV-20251203-001"
    verified_by: "runtime_feedback_agent"
    metrics_normalized: true
```

### 8.3 Homeostasis Model Updates

```yaml
# File: .ai-workspace/observability/homeostasis_updates.yml

homeostasis_updates:
  - update_id: "HM-20251203-001"
    timestamp: "2025-12-03T00:00:00Z"
    update_type: "baseline_recalculation"
    req_id: "REQ-NFR-PERF-001"

    changes:
      baseline:
        p95_latency_ms:
          old: 240
          new: 235
          reason: "30-day rolling average recalculated"

    sample_period: "2025-11-03 to 2025-12-03"
    data_points: 43200

  - update_id: "HM-20251203-002"
    timestamp: "2025-12-03T16:00:00Z"
    update_type: "threshold_adjustment"
    req_id: "REQ-NFR-PERF-001"

    changes:
      thresholds:
        p95_latency_ms:
          warning:
            old: 400
            new: 350
            reason: "Tightening SLA after optimization"

    approved_by: "tech.lead@company.com"
    effective_date: "2025-12-04T00:00:00Z"
```

---

## 9. Implementation Guidance

### 9.1 Phase 1: Telemetry Tagging (Week 1)

**Goal**: Instrument code with REQ-* tags

**Tasks**:
1. Create structured logging wrapper
2. Create metrics wrapper (Datadog/Prometheus)
3. Update existing code to add tags
4. Configure log aggregation
5. Verify tags in observability platform

**Deliverables**:
- `logging_config.py` (structured logging)
- `metrics.py` (tagged metrics)
- Code updated with REQ tags
- Datadog/Prometheus dashboards showing tagged data

### 9.2 Phase 2: Homeostasis Model (Week 2)

**Goal**: Define expected behavior from requirements

**Tasks**:
1. Extract thresholds from NFR requirements
2. Calculate baselines from production data
3. Create homeostasis model file
4. Implement threshold extraction algorithm
5. Implement baseline calculator

**Deliverables**:
- `homeostasis_model.yml`
- `homeostasis_extractor.py`
- `baseline_calculator.py`
- Documentation on adding new requirements

### 9.3 Phase 3: Deviation Detection (Week 3)

**Goal**: Detect deviations from homeostasis

**Tasks**:
1. Implement deviation detector
2. Implement severity classifier
3. Configure alerts in observability platform
4. Test detection with synthetic deviations
5. Tune thresholds and cooldowns

**Deliverables**:
- `deviation_detector.py`
- `alert_generator.py`
- Datadog/Prometheus alert rules
- Detection accuracy report

### 9.4 Phase 4: Intent Generation (Week 4)

**Goal**: Auto-generate intents from deviations

**Tasks**:
1. Implement Runtime Feedback Agent
2. Create intent templates for deviations
3. Implement cooldown tracking
4. Test end-to-end flow
5. Configure notification channels

**Deliverables**:
- `runtime_feedback_agent.py`
- Intent templates
- Notification service
- End-to-end test suite

### 9.5 Phase 5: Integration & Deployment (Week 5)

**Goal**: Deploy to production with monitoring

**Tasks**:
1. Deploy webhook handlers
2. Configure observability platform webhooks
3. Set up notification channels (Slack, email)
4. Monitor feedback loop performance
5. Create runbooks and documentation

**Deliverables**:
- Deployed webhook service
- Configured observability integrations
- Slack/email notifications working
- Operational runbooks
- User documentation

### 9.6 Testing Strategy

**Unit Tests**:
- Tag extraction from various formats
- Threshold comparison logic
- Severity classification
- Intent generation

**Integration Tests**:
- Alert payload → Deviation detection
- Deviation → Intent generation
- Intent → Requirements stage flow
- Webhook handlers

**End-to-End Tests**:
- Simulate production alert
- Verify deviation detection
- Verify intent creation
- Verify notification delivery
- Verify feedback loop closure

**Load Tests**:
- High alert volume handling
- Cooldown effectiveness
- Webhook handler performance

---

## 10. Examples

### 10.1 Complete Feedback Loop Example

#### Step 1: Code with Telemetry Tags

```python
# src/auth/login.py

# Implements: REQ-F-AUTH-001, REQ-NFR-PERF-001
def login(email: str, password: str) -> LoginResult:
    """User login with email and password"""
    start_time = time.time()

    try:
        user = authenticate(email, password)

        latency_ms = (time.time() - start_time) * 1000

        logger.info(
            "Login successful",
            extra={
                "req": "REQ-F-AUTH-001",
                "user_id": user.id,
                "latency_ms": latency_ms
            }
        )

        metrics.histogram(
            "auth.login.latency",
            latency_ms,
            req="REQ-NFR-PERF-001"
        )

        return LoginResult(success=True, user=user)
    except Exception as e:
        logger.error(
            "Login failed",
            extra={"req": "REQ-F-AUTH-001", "error": str(e)}
        )
        raise
```

#### Step 2: Homeostasis Model

```yaml
REQ-NFR-PERF-001:
  thresholds:
    p95_latency_ms:
      critical: 500
      warning: 400
  baseline:
    p95_latency_ms: 235
  deviation_rules:
    - condition: "value > 500"
      severity: "critical"
      action: "generate_intent"
```

#### Step 3: Production Alert

```json
{
  "alert_id": "12345",
  "title": "REQ-NFR-PERF-001: High latency",
  "tags": ["req:REQ-NFR-PERF-001"],
  "current_value": 850,
  "threshold": 500,
  "timestamp": "2025-12-03T14:32:15Z"
}
```

#### Step 4: Deviation Detection

```python
deviation = DeviationDetector.detect(alert)
# Result:
# Deviation(
#   req_id="REQ-NFR-PERF-001",
#   deviation_type=PERFORMANCE_DEGRADATION,
#   severity=CRITICAL,
#   current_value=850,
#   threshold=500,
#   baseline=235,
#   deviation_pct=261.7%
# )
```

#### Step 5: Intent Generation

```yaml
# File: .ai-workspace/intents/human/INT-20251203-042.yml

id: INT-20251203-042
classification:
  work_type: remediate
  priority: critical
title: "[RUNTIME] REQ-NFR-PERF-001: Performance Degradation"
description: |
  🚨 AUTOMATICALLY GENERATED FROM RUNTIME FEEDBACK

  P95 latency is 850ms (threshold: 500ms, baseline: 235ms)
  Deviation: +261.7% from baseline

  Root cause investigation needed.
source:
  type: runtime_feedback
status: draft
```

#### Step 6: Human Review

```yaml
status: approved
status_history:
  - status: approved
    author: "john.doe@company.com"
    comment: "Confirmed performance issue, proceeding with fix"
```

#### Step 7: Requirements Stage

```markdown
## REQ-F-PERF-FIX-001: Fix Login Performance Regression

**Derived From**: INT-20251203-042
**Type**: Remediation
**Priority**: Critical

**Description**: Investigate and fix performance regression in login endpoint.

**Root Cause**: TBD (under investigation)

**Acceptance Criteria**:
- AC-001: P95 latency returns to < 500ms
- AC-002: Baseline performance restored (~235ms)
- AC-003: No regression in related functionality
- AC-004: Root cause documented
- AC-005: Preventive measures implemented
```

#### Step 8: Fix Deployed

```python
# Code fix deployed
# Metrics return to normal
# Runtime Feedback Agent detects resolution
```

#### Step 9: Deviation Resolved

```yaml
# File: .ai-workspace/observability/deviation_history/REQ-NFR-PERF-001_HISTORY.yml

deviations:
  - deviation_id: "DEV-20251203-001"
    detected_at: "2025-12-03T14:32:15Z"
    resolved_at: "2025-12-03T15:45:00Z"
    intent_generated: INT-20251203-042
    resolution:
      root_cause: "Database connection pool exhaustion"
      fix: "Released connections before external API calls"
```

### 10.2 Feedback Loop Without Intent (Warning Level)

```yaml
# Alert received
alert:
  severity: warning
  current_value: 450
  threshold: 500

# Deviation detected
deviation:
  severity: HIGH
  deviation_pct: 87.5%

# Action: Alert only, no intent
action: alert_only

# Logged to deviation history
# No intent generated (below critical threshold)
```

---

## ADR References

- **ADR-005**: Iterative Refinement Feedback Loops (runtime feedback protocol)

---

## Implementation Checklist

- [ ] Structured logging with REQ tags (Python, JS)
- [ ] Metrics wrapper with REQ tags (Datadog, Prometheus)
- [ ] Homeostasis model schema
- [ ] Threshold extraction algorithm
- [ ] Baseline calculator
- [ ] Deviation detector
- [ ] Severity classifier
- [ ] Alert generator
- [ ] Runtime Feedback Agent
- [ ] Intent generation logic
- [ ] Cooldown tracker
- [ ] Webhook handlers (Datadog, Prometheus)
- [ ] Notification service (Slack, email)
- [ ] Deviation history storage
- [ ] Feedback audit trail
- [ ] Unit tests (90%+ coverage)
- [ ] Integration tests
- [ ] End-to-end tests
- [ ] Load tests
- [ ] Documentation complete
- [ ] Runbooks created
- [ ] Architecture review approved
- [ ] Security review approved

---

**Last Updated**: 2025-12-03
**Owned By**: Design Agent (Runtime Feedback System)
