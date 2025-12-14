# Implements: REQ-RUNTIME-002 (Deviation Detection)
"""
Deviation Detector

Detects deviations from the homeostasis model.
"""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum
import re


class DeviationType(Enum):
    """Types of runtime deviations"""
    PERFORMANCE_DEGRADATION = "performance_degradation"
    ERROR_RATE_INCREASE = "error_rate_increase"
    SLA_BREACH = "sla_breach"
    AVAILABILITY_LOSS = "availability_loss"


class Severity(Enum):
    """Deviation severity levels"""
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


REQ_TAG_PATTERN = re.compile(r'REQ-(F|NFR|DATA|BR)-[A-Z]{2,10}-\d{3}')


def extract_req_tags(data: dict | str) -> List[str]:
    """
    Extract requirement tags from telemetry data.

    Args:
        data: Dictionary (log entry, alert payload) or string

    Returns:
        List of unique REQ-* tags found
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
                        # Handle "req:REQ-NFR-PERF-001" format
                        if ':' in str(tag):
                            tag_value = str(tag).split(':', 1)[1]
                            found = REQ_TAG_PATTERN.match(tag_value)
                            if found:
                                all_tags.append(tag_value)
                        else:
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
        metric_name = self._extract_metric_name(alert, req_model)

        if current_value is None or not metric_name:
            return None

        # Get threshold and baseline
        thresholds = req_model.get('thresholds', {}).get(metric_name, {})
        baseline = req_model.get('baseline', {}).get(metric_name, 0)

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
            req_model.get('type', 'performance'),
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
            detected_at=alert.get('timestamp', ''),
            telemetry_links=self._extract_telemetry_links(alert),
            context={
                'alert_id': alert.get('alert_id'),
                'service': alert.get('service'),
                'environment': alert.get('environment')
            }
        )

    def _extract_metric_name(self, alert: dict, req_model: dict) -> Optional[str]:
        """Extract metric name from alert query or model"""
        # Simple heuristic: use first threshold key
        thresholds = req_model.get('thresholds', {})
        if thresholds:
            return list(thresholds.keys())[0]

        return None

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

        # Critical: exceeds critical threshold
        if critical and value >= critical:
            return Severity.CRITICAL
        # High: exceeds warning threshold
        elif warning and value >= warning:
            return Severity.HIGH
        # Medium: significant deviation from baseline but within thresholds
        elif baseline > 0 and abs(value - baseline) / baseline > 0.5:
            # But if still within warning threshold, it's just medium
            if warning and value < warning:
                return Severity.MEDIUM
            return Severity.HIGH  # Deviation + close to warning
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
