# Validates: REQ-RUNTIME-003 (Feedback Loop Closure)
"""
Test suite for Runtime Feedback Agent.

Tests the complete feedback loop from production deviations to intent generation.
"""

import pytest
from datetime import datetime
from enum import Enum


# Implements: REQ-RUNTIME-003
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


class TestRuntimeFeedbackAgent:
    """Test Runtime Feedback Agent - closes the governance loop"""

    def test_process_critical_alert_generates_intent(self):
        """
        Validates: REQ-RUNTIME-003
        RED phase test - should fail (no implementation yet)

        Given a critical performance deviation alert
        When the Runtime Feedback Agent processes it
        Then an intent should be auto-generated
        And stakeholders should be notified
        """
        # Arrange: Create critical alert payload
        alert_payload = {
            'alert_id': 'ALERT-12345',
            'title': 'REQ-NFR-PERF-001: High latency',
            'tags': ['req:REQ-NFR-PERF-001'],
            'current_value': 850,  # milliseconds
            'threshold': 500,      # SLA limit
            'timestamp': '2025-12-15T14:32:15Z',
            'service': 'auth-service',
            'environment': 'production'
        }

        homeostasis_model = {
            'requirements': {
                'REQ-NFR-PERF-001': {
                    'title': 'Login response time < 500ms',
                    'type': 'performance',
                    'thresholds': {
                        'p95_latency_ms': {
                            'critical': 500,
                            'warning': 400,
                            'target': 250
                        }
                    },
                    'baseline': {
                        'p95_latency_ms': 235
                    },
                    'deviation_rules': [{
                        'metric': 'p95_latency_ms',
                        'condition': 'value > threshold.critical',
                        'severity': 'critical',
                        'action': 'generate_intent'
                    }]
                }
            }
        }

        # Mock dependencies
        intent_manager = MockIntentManager()
        notification_service = MockNotificationService()

        # Act: Process alert
        from runtime_feedback.runtime_feedback_agent import RuntimeFeedbackAgent

        agent = RuntimeFeedbackAgent(
            homeostasis_model=homeostasis_model,
            intent_manager=intent_manager,
            notification_service=notification_service
        )

        intent_id = agent.process_alert(alert_payload)

        # Assert: Intent should be generated
        assert intent_id is not None
        assert intent_id.startswith('INT-')

        # Assert: Intent created with correct data
        created_intent = intent_manager.get_intent(intent_id)
        assert created_intent is not None
        assert created_intent['classification']['work_type'] == 'remediate'
        assert created_intent['classification']['priority'] == 'critical'
        assert 'REQ-NFR-PERF-001' in created_intent['incident']['affected_requirements']
        assert created_intent['incident']['severity'] == 'critical'

        # Assert: Notification sent
        assert notification_service.was_notified()
        notification = notification_service.get_last_notification()
        assert 'REQ-NFR-PERF-001' in notification['message']


    def test_process_warning_alert_does_not_generate_intent(self):
        """
        Validates: REQ-RUNTIME-003

        Given a warning-level deviation (not critical)
        When the Runtime Feedback Agent processes it
        Then an alert should be sent but NO intent generated
        """
        # Arrange
        alert_payload = {
            'alert_id': 'ALERT-12346',
            'title': 'REQ-NFR-PERF-001: Elevated latency',
            'tags': ['req:REQ-NFR-PERF-001'],
            'current_value': 450,  # Above baseline, below critical
            'threshold': 500,
            'timestamp': '2025-12-15T14:35:00Z'
        }

        homeostasis_model = {
            'requirements': {
                'REQ-NFR-PERF-001': {
                    'thresholds': {
                        'p95_latency_ms': {
                            'critical': 500,
                            'warning': 400
                        }
                    },
                    'baseline': {
                        'p95_latency_ms': 235
                    }
                }
            }
        }

        intent_manager = MockIntentManager()
        notification_service = MockNotificationService()

        # Act
        from runtime_feedback.runtime_feedback_agent import RuntimeFeedbackAgent

        agent = RuntimeFeedbackAgent(
            homeostasis_model=homeostasis_model,
            intent_manager=intent_manager,
            notification_service=notification_service
        )

        intent_id = agent.process_alert(alert_payload)

        # Assert: No intent generated
        assert intent_id is None

        # Assert: Notification still sent (alert-only)
        assert notification_service.was_notified()


    def test_cooldown_prevents_intent_spam(self):
        """
        Validates: REQ-RUNTIME-003

        Given multiple critical alerts for the same requirement
        When they occur within the cooldown period
        Then only the first should generate an intent
        """
        # Arrange
        alert_payload = {
            'alert_id': 'ALERT-12347',
            'tags': ['req:REQ-NFR-PERF-001'],
            'current_value': 850,
            'threshold': 500
        }

        homeostasis_model = {
            'requirements': {
                'REQ-NFR-PERF-001': {
                    'thresholds': {
                        'p95_latency_ms': {
                            'critical': 500
                        }
                    },
                    'baseline': {
                        'p95_latency_ms': 235
                    }
                }
            }
        }

        intent_manager = MockIntentManager()
        notification_service = MockNotificationService()

        from runtime_feedback.runtime_feedback_agent import RuntimeFeedbackAgent

        agent = RuntimeFeedbackAgent(
            homeostasis_model=homeostasis_model,
            intent_manager=intent_manager,
            notification_service=notification_service
        )

        # Act: Process same alert twice
        intent_id_1 = agent.process_alert(alert_payload)
        intent_id_2 = agent.process_alert(alert_payload)  # Within cooldown

        # Assert: Only first generates intent
        assert intent_id_1 is not None
        assert intent_id_2 is None

        # Assert: Only one intent created
        assert len(intent_manager.get_all_intents()) == 1


# Mock classes for testing

class MockIntentManager:
    """Mock Intent Manager for testing"""

    def __init__(self):
        self.intents = {}
        self.counter = 1

    def create_intent(self, intent_data):
        """Create a new intent"""
        intent_id = f"INT-{datetime.now().strftime('%Y%m%d')}-{self.counter:03d}"
        self.counter += 1

        self.intents[intent_id] = {
            'id': intent_id,
            **intent_data
        }

        return intent_id

    def get_intent(self, intent_id):
        """Retrieve an intent"""
        return self.intents.get(intent_id)

    def get_all_intents(self):
        """Get all intents"""
        return list(self.intents.values())


class MockNotificationService:
    """Mock Notification Service for testing"""

    def __init__(self):
        self.notifications = []

    def send(self, alert):
        """Send notification"""
        self.notifications.append(alert)

    def send_with_intent(self, alert, intent_id):
        """Send notification with intent"""
        alert['intent_id'] = intent_id
        self.notifications.append(alert)

    def was_notified(self):
        """Check if any notification was sent"""
        return len(self.notifications) > 0

    def get_last_notification(self):
        """Get last notification"""
        return self.notifications[-1] if self.notifications else None
