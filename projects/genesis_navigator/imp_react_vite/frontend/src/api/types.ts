// Implements: REQ-F-API-001, REQ-F-API-002, REQ-F-API-003, REQ-F-API-004

export type ProjectState = 'ITERATING' | 'QUIESCENT' | 'CONVERGED' | 'BOUNDED'

export interface ProjectSummary {
  project_id: string
  name: string
  root_path: string
  state: ProjectState
  feature_count: number
  converged_count: number
  iterating_count: number
  blocked_count: number
  event_count: number
  last_event_at: string | null
}

export interface EdgeTrajectory {
  edge: string
  status: 'pending' | 'iterating' | 'converged' | 'blocked'
  iteration: number
  delta: number | null
  started_at: string | null
  converged_at: string | null
}

export interface FeatureDetail {
  feature_id: string
  title: string
  status: string
  priority: string
  satisfies: string[]
  trajectory: EdgeTrajectory[]
  hamiltonian_t: number
  hamiltonian_v: number
  hamiltonian_h: number
}

export interface ProjectDetail {
  project_id: string
  name: string
  root_path: string
  state: ProjectState
  features: FeatureDetail[]
  last_event_at: string | null
}

export interface GapItem {
  req_key: string
  layer: number
  severity: 'high' | 'medium' | 'low'
  description: string
  affected_files: string[]
}

export interface GapLayer {
  layer: number
  name: string
  status: 'pass' | 'fail' | 'advisory'
  gap_count: number
  gaps: GapItem[]
}

export interface GapReport {
  project_id: string
  layers: GapLayer[]
  total_req_keys: number
  covered_count: number
  gap_count: number
}

export type QueueItemType = 'STUCK' | 'BLOCKED' | 'GAP_CLUSTER' | 'IN_PROGRESS'

export interface QueueItem {
  item_type: QueueItemType
  feature_id: string
  title: string
  edge: string | null
  priority: number
  description: string
  blocked_by: string | null
  delta: number | null
  consecutive_failures: number
  affected_req_keys: string[]
}
