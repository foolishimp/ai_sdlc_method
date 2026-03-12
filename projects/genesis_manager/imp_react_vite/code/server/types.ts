// Implements: REQ-DATA-WORK-002, REQ-F-PROJ-004, REQ-F-OVR-001, REQ-F-SUP-001, REQ-F-EVI-001
// Server-side shared types for the genesis_manager Express server (Node.js context)

// ---------------------------------------------------------------------------
// Core registration
// ---------------------------------------------------------------------------

export interface WorkspaceRegistration {
  id: string;
  path: string;
  name: string;
}

// ---------------------------------------------------------------------------
// Inbound event payload from API clients
// ---------------------------------------------------------------------------

export interface EventPayloadIn {
  event_type: string;
  feature?: string;
  edge?: string;
  actor?: string;
  comment?: string;
  data?: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Custom error types
// ---------------------------------------------------------------------------

export class WriteError extends Error {
  code: 'LOCK_TIMEOUT' | 'IO_ERROR' | 'INVALID_PAYLOAD';

  constructor(
    message: string,
    code: 'LOCK_TIMEOUT' | 'IO_ERROR' | 'INVALID_PAYLOAD',
  ) {
    super(message);
    this.name = 'WriteError';
    this.code = code;
  }
}

export class ReadError extends Error {
  code: 'NOT_FOUND' | 'INVALID_FORMAT' | 'IO_ERROR';

  constructor(
    message: string,
    code: 'NOT_FOUND' | 'INVALID_FORMAT' | 'IO_ERROR',
  ) {
    super(message);
    this.name = 'ReadError';
    this.code = code;
  }
}

// ---------------------------------------------------------------------------
// Domain types (server-side, mirrored from client src/api/types.ts)
// ---------------------------------------------------------------------------

export interface WorkspaceEvent {
  event_type: string;
  timestamp: string;
  feature?: string;
  edge?: string;
  [key: string]: unknown;
}

export interface WorkspaceSummary {
  id: string;
  path: string;
  name: string;
  pendingGates: number;
  stuckFeatures: number;
  lastEventAt: string | null;
}

export interface GateItem {
  id: string;
  feature: string;
  edge: string;
  requestedAt: string;
  isStuck: boolean;
}

export interface FeatureVector {
  feature: string;
  title: string;
  status: string;
  trajectory: Record<string, { status: string; iteration: number }>;
}

export interface WorkspaceOverview {
  workspaceId: string;
  projectName: string;
  features: FeatureVector[];
  recentEvents: WorkspaceEvent[];
  lastRefreshed: string;
}

export interface TraceabilityEntry {
  reqKey: string;
  kind: 'implements' | 'validates';
  filePath: string;
  lineNumber: number;
}
