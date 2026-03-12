// Implements: REQ-F-API-001, REQ-F-API-002, REQ-F-API-003, REQ-F-API-004, REQ-F-FEATDETAIL-001, REQ-F-HIST-001, REQ-F-HIST-002

export type ProjectState = 'ITERATING' | 'QUIESCENT' | 'CONVERGED' | 'BOUNDED'

export interface ProjectSummary {
  project_id: string
  name: string
  path: string
  state: ProjectState
  active_feature_count: number
  converged_feature_count: number
  last_event_at: string | null
  scan_duration_ms: number
}

export interface EdgeTrajectory {
  edge: string
  status: 'in_progress' | 'converged' | 'blocked' | 'pending'
  iteration: number
  delta: number
  started_at: string | null
  converged_at: string | null
}

export interface Hamiltonian {
  H: number
  T: number
  V: number
  flat: boolean
}

export interface FeatureDetail {
  feature_id: string
  title: string
  status: string
  current_edge: string | null
  delta: number
  hamiltonian: Hamiltonian
  trajectory: EdgeTrajectory[]
  error: string | null
  satisfies?: string[]
  acceptance_criteria?: string[]
}

export interface ProjectDetail {
  project_id: string
  name: string
  state: ProjectState
  features: FeatureDetail[]
  total_edges: number
  converged_edges: number
}

export interface BackendGapItem {
  req_key: string
  gap_type: string
  files: string[]
  suggested_command: string | null
}

export interface BackendGapLayer {
  gap_count: number
  coverage_pct: number
  gaps: BackendGapItem[]
}

export interface GapReport {
  project_id: string
  computed_at: string
  health_signal: string
  layer_1: BackendGapLayer
  layer_2: BackendGapLayer
  layer_3: BackendGapLayer
}

export interface QueueItemDetail {
  reason: string
  delta: number | null
  failing_checks: string[]
  expected_outcome: string
  gap_keys: string[]
  iteration_history: unknown[]
}

export type QueueItemType = 'STUCK' | 'BLOCKED' | 'GAP_CLUSTER' | 'IN_PROGRESS'

export interface QueueItem {
  type: QueueItemType
  severity: 'high' | 'medium' | 'low'
  feature_id: string | null
  description: string
  command: string
  detail: QueueItemDetail
}

export type RunFinalState = 'ITERATING' | 'CONVERGED' | 'UNINITIALIZED'

export interface RunSummary {
  run_id: string
  timestamp: string | null
  event_count: number
  edges_traversed: number
  final_state: RunFinalState
  is_current: boolean
}

export interface RunEvent {
  event_type: string
  timestamp: string | null
  feature: string | null
  edge: string | null
  data: Record<string, unknown>
}

export interface RunSegment {
  feature: string | null
  edge: string | null
  events: RunEvent[]
}

export interface RunTimeline {
  run_id: string
  event_count: number
  segments: RunSegment[]
}
