"""Read-only readers for Genesis workspace data.

All readers are pure read operations — no writes, no side effects (REQ-NFR-ARCH-002).
"""

# Implements: REQ-F-STAT-001, REQ-F-STAT-002, REQ-F-STAT-003, REQ-F-STAT-004
# Implements: REQ-NFR-ARCH-002

from genesis_nav.readers.event_reader import last_event_timestamp, read_events
from genesis_nav.readers.feature_reader import read_features
from genesis_nav.readers.state_computer import (
    build_feature_detail,
    compute_hamiltonian,
    compute_project_state,
)

__all__ = [
    "read_events",
    "last_event_timestamp",
    "read_features",
    "compute_project_state",
    "compute_hamiltonian",
    "build_feature_detail",
]
