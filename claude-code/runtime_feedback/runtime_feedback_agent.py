# Implements: REQ-RUNTIME-003 (Feedback Loop Closure)
"""
Runtime Feedback Agent

Closes the governance loop by monitoring production and generating intents
when deviations from expected behavior are detected.

This module implements the core feedback loop:
    Production Metrics → Deviation Detection → Intent Generation → Requirements Stage

Performance: < 1s per alert processing (REQ-NFR-REFINE-001)
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from .deviation_detector import DeviationDetector, Severity, DeviationType, Deviation

logger = logging.getLogger(__name__)


class RuntimeFeedbackAgent:
    """
    Agent that closes the feedback loop from production to requirements.

    This agent:
    1. Receives alerts from observability platforms
    2. Detects deviations from homeostasis model
    3. Generates intents for critical deviations
    4. Notifies stakeholders
    5. Prevents intent spam via cooldown
    """

    def __init__(
        self,
        homeostasis_model: dict,
        intent_manager,
        notification_service
    ):
        """
        Initialize Runtime Feedback Agent.

        Args:
            homeostasis_model: Expected behavior model from requirements
            intent_manager: Service for creating intents
            notification_service: Service for sending notifications
        """
        self.detector = DeviationDetector(homeostasis_model)
        self.intent_manager = intent_manager
        self.notification_service = notification_service
        self.cooldown_tracker = {}  # Track recent intents to prevent spam

    def process_alert(self, alert_payload: Dict[str, Any]) -> Optional[str]:
        """
        Process alert and potentially generate intent.

        Implements: REQ-RUNTIME-003 (Feedback Loop Closure)

        Flow:
            1. Detect deviation from homeostasis model
            2. Classify severity (CRITICAL/HIGH/MEDIUM/LOW)
            3. Generate intent if CRITICAL
            4. Send notification
            5. Track cooldown to prevent spam

        Args:
            alert_payload: Alert from observability platform (Datadog/Prometheus)
                          Must include: alert_id, tags (with req:REQ-*), current_value

        Returns:
            Intent ID if generated (INT-YYYYMMDD-NNN), None otherwise

        Performance: < 1s (REQ-NFR-REFINE-001)
        """
        try:
            start_time = datetime.now()

            # Step 1: Detect deviation
            deviation = self.detector.detect(alert_payload)

            if not deviation:
                logger.debug(
                    "No deviation detected for alert",
                    extra={'alert_id': alert_payload.get('alert_id')}
                )
                return None

            logger.info(
                "Deviation detected",
                extra={
                    'req': deviation.req_id,
                    'severity': deviation.severity.value,
                    'deviation_pct': f"{deviation.deviation_percentage:+.1f}%"
                }
            )

            # Step 2: Check if intent generation is warranted
            should_generate = self._should_generate_intent(deviation)

            if not should_generate:
                # Just alert, don't generate intent
                alert = self._create_alert(deviation, alert_payload)
                self.notification_service.send(alert)

                logger.info(
                    "Alert sent (no intent generated)",
                    extra={
                        'req': deviation.req_id,
                        'severity': deviation.severity.value,
                        'reason': 'below_critical_threshold'
                    }
                )
                return None

            # Step 3: Check cooldown (prevent intent spam)
            if self._is_in_cooldown(deviation.req_id):
                logger.info(
                    "Intent generation skipped (cooldown active)",
                    extra={
                        'req': deviation.req_id,
                        'reason': 'cooldown'
                    }
                )
                return None

            # Step 4: Generate intent
            intent_id = self._generate_intent(deviation, alert_payload)

            # Step 5: Track cooldown
            self._record_intent_generation(deviation.req_id)

            # Step 6: Notify stakeholders
            alert = self._create_alert(deviation, alert_payload)
            self.notification_service.send_with_intent(alert, intent_id)

            # Log performance
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

            logger.info(
                "Intent generated from runtime feedback",
                extra={
                    'req': deviation.req_id,
                    'intent_id': intent_id,
                    'severity': deviation.severity.value,
                    'latency_ms': elapsed_ms
                }
            )

            return intent_id

        except Exception as e:
            logger.error(
                "Failed to process alert",
                exc_info=True,
                extra={
                    'alert_id': alert_payload.get('alert_id'),
                    'error': str(e)
                }
            )
            # Don't raise - failed alert processing shouldn't crash service
            return None

    def _should_generate_intent(self, deviation) -> bool:
        """
        Determine if deviation warrants intent generation.

        Only CRITICAL severity generates intent automatically.
        HIGH/MEDIUM/LOW send alerts only (no intent).
        """
        # Only critical severity generates intent
        if deviation.severity == Severity.CRITICAL:
            return True

        # High/Medium/Low only alert
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

    def _create_alert(self, deviation, alert_payload: dict) -> dict:
        """Create alert payload for notification"""
        return {
            'alert_type': 'deviation_detected',
            'req_id': deviation.req_id,
            'severity': deviation.severity.value,
            'title': f"{deviation.req_id}: {deviation.deviation_type.value.replace('_', ' ').title()}",
            'message': self._format_alert_message(deviation),
            'telemetry_links': deviation.telemetry_links,
            'detected_at': deviation.detected_at
        }

    def _format_alert_message(self, deviation) -> str:
        """Format alert message"""
        return f"""Deviation Detected: {deviation.req_id}

Type: {deviation.deviation_type.value.replace('_', ' ').title()}
Severity: {deviation.severity.value.upper()}

Metric: {deviation.metric_name}
Current Value: {deviation.current_value:.2f}
Threshold: {deviation.threshold_value:.2f}
Baseline: {deviation.baseline_value:.2f}
Deviation: {deviation.deviation_percentage:+.1f}%

Detected: {deviation.detected_at}

Context:
- Service: {deviation.context.get('service', 'unknown')}
- Environment: {deviation.context.get('environment', 'unknown')}
- Alert ID: {deviation.context.get('alert_id', 'N/A')}
"""

    def _generate_intent(self, deviation, alert_payload: dict) -> str:
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

    def _format_intent_description(self, deviation, alert: dict) -> str:
        """Format intent description"""
        return f"""🚨 AUTOMATICALLY GENERATED FROM RUNTIME FEEDBACK

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
"""
