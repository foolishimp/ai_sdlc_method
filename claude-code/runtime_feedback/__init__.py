# Implements: REQ-RUNTIME-003 (Feedback Loop Closure)
"""
Runtime Feedback Module

Closes the governance loop from production to requirements.
"""

from .runtime_feedback_agent import RuntimeFeedbackAgent
from .deviation_detector import DeviationDetector, Deviation, DeviationType, Severity

__all__ = [
    'RuntimeFeedbackAgent',
    'DeviationDetector',
    'Deviation',
    'DeviationType',
    'Severity'
]
