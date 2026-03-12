// Implements: REQ-F-PROJ-001, REQ-DATA-WORK-001
// All shared domain types for genesis_manager browser SPA ↔ Express server

// ─── Workspace / Project ──────────────────────────────────────────────────────

export interface RegisteredWorkspace {
  id: string
  absolutePath: string
  name: string
  available: boolean
  lastChecked: string // ISO 8601
}

export interface WorkspaceSummary {
  workspaceId: string
  projectName: string
  activeFeatureCount: number
  pendingGateCount: number
  stuckFeatureCount: number
  lastEventTimestamp: string | null // ISO 8601
  hasAttentionRequired: boolean
  available: boolean
}

// ─── Overview ─────────────────────────────────────────────────────────────────

export interface FeatureStatusSummary {
  converged: number
  in_progress: number
  blocked: number
  pending: number
  pendingGates: number
}

export interface InProgressFeature {
  featureId: string
  title: string
  currentEdge: string
  iterationNumber: number
  delta: number
  lastEventAt: string // ISO 8601
}

export interface RecentActivity {
  featureId: string
  edge: string
  iterationNumber: number
  timestamp: string // ISO 8601
  delta: number
  runId: string | null
}

export interface WorkspaceOverview {
  projectName: string
  methodVersion: string
  statusCounts: FeatureStatusSummary
  inProgressFeatures: InProgressFeature[]
  recentActivity: RecentActivity | null
  featureLastEvents: Record<string, string> // featureId → ISO timestamp
  pendingGateCount: number
}

// ─── Gates / Supervision ──────────────────────────────────────────────────────

export interface GateItem {
  id: string // composite: featureId:edge:gateName
  featureId: string
  edge: string
  gateName: string
  pendingSince: string // ISO 8601
  ageMs: number
}

export interface SupervisionFeature {
  featureId: string
  title: string
  currentEdge: string
  iterationNumber: number
  delta: number
  status: 'converged' | 'stuck' | 'blocked' | 'in_progress' | 'pending'
  consecutiveStuckIterations?: number
  blockReason?: 'human_gate' | 'spawn_dependency' | 'other'
  blockingChildFeatureId?: string
  blockingGate?: GateItem
  timeBlockedMs?: number
  autoModeEnabled: boolean
}

export interface GateDecision {
  featureId: string
  edge: string
  gateName: string
  decision: 'approved' | 'rejected'
  comment?: string
}

// ─── Feature Vectors ──────────────────────────────────────────────────────────

export interface FeatureVector {
  featureId: string
  title: string
  status: 'converged' | 'in_progress' | 'blocked' | 'pending'
  currentEdge: string | null
  currentDelta: number | null
  satisfies: string[] // REQ-* keys
  childVectors: string[]
}

// ─── Feature Trajectory (for NavHandle detail page) ───────────────────────────

export interface FeatureTrajectory {
  featureId: string
  title: string
  status: 'converged' | 'in_progress' | 'blocked' | 'pending'
  currentEdge: string | null
  currentDelta: number | null
  edges: EdgeStatus[]
  events: WorkspaceEvent[]
  childVectors: string[]
  satisfies: string[]
}

export interface EdgeStatus {
  edge: string
  status: 'converged' | 'in_progress' | 'pending' | 'not_started'
  iterationCount: number
  delta: number | null
  lastRunId: string | null
}

// ─── Traceability ─────────────────────────────────────────────────────────────

export interface TraceabilityEntry {
  reqKey: string
  taggedInCode: boolean
  taggedInTests: boolean
  codeFiles: string[]
  testFiles: string[]
}

// ─── Events ───────────────────────────────────────────────────────────────────

export interface WorkspaceEvent {
  eventIndex: number // line index in events.jsonl — stable
  eventType: string
  timestamp: string // ISO 8601
  feature: string | null
  edge: string | null
  iteration: number | null
  delta: number | null
  runId: string | null
  raw: Record<string, unknown>
}

export interface EventPayload {
  event_type: string
  feature?: string
  edge?: string
  gate_name?: string
  decision?: 'approved' | 'rejected'
  comment?: string
  actor?: string
  enabled?: boolean
  child_type?: string
  parent_feature?: string
  reason?: string
  [key: string]: unknown
}

// ─── Gap Analysis ─────────────────────────────────────────────────────────────

export interface GapEntry {
  reqKey: string
  description: string
  targetPath: string | null
}

export interface GapLayer {
  status: 'PASS' | 'ADVISORY' | 'FAIL'
  coveredCount: number
  totalCount: number
  gaps: GapEntry[]
}

export interface GapAnalysisData {
  runAt: string | null
  l1: GapLayer | null
  l2: GapLayer | null
  l3: GapLayer | null
}

// ─── Filesystem Browse (REQ-F-FSNAV-001) ─────────────────────────────────────

export interface FsEntry {
  name: string
  absolutePath: string
  isDir: true
  hasWorkspace: boolean
}

export interface FsBrowseResult {
  path: string
  parent: string | null
  entries: FsEntry[]
  truncated?: boolean
}

// ─── Errors ───────────────────────────────────────────────────────────────────

export interface ApiError {
  status: number
  message: string
}
