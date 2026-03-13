// Implements: REQ-F-PROJ-001, REQ-F-OVR-001, REQ-F-SUP-001, REQ-NFR-REL-001
// Reads Genesis workspace artifacts (project_constraints.yml, feature vectors,
// events.jsonl) and assembles typed summary / overview / gate / feature objects.

import fs from 'node:fs/promises';
import { Dirent } from 'node:fs';
import path from 'node:path';
import yaml from 'js-yaml';
import { readAll, computeIsStuck, computeAutoMode } from './EventLogReader.js';
import type {
  WorkspaceSummary,
  WorkspaceOverview,
  GateItem,
  BlockedFeatureSummary,
  FeatureVector,
  WorkspaceEvent,
  InProgressFeature,
  RecentActivity,
} from '../types.js';

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

/**
 * Read and parse project_constraints.yml from inside .ai-workspace/.
 * Returns "unknown" for name if the file is absent or malformed.
 */
async function readProjectName(workspacePath: string): Promise<string> {
  const constraintsPath = path.join(workspacePath, 'project_constraints.yml');
  try {
    const raw = await fs.readFile(constraintsPath, 'utf-8');
    const doc = yaml.load(raw) as Record<string, unknown> | null;
    if (doc) {
      if (typeof doc['project_name'] === 'string') return doc['project_name'];
      if (typeof doc['name'] === 'string') return doc['name'];
    }
  } catch {
    // fall through to path-based name
  }
  // Fall back to the parent directory name of the .ai-workspace path
  return path.basename(path.dirname(workspacePath));
}

/**
 * Collect all YAML files from features/active/ and features/completed/ within
 * the workspace. Returns raw parsed YAML documents (unknown shape from disk).
 */
async function readFeatureYamls(
  workspacePath: string,
): Promise<Array<Record<string, unknown>>> {
  const dirs = [
    path.join(workspacePath, 'features', 'active'),
    path.join(workspacePath, 'features', 'completed'),
  ];

  const results: Array<Record<string, unknown>> = [];

  for (const dir of dirs) {
    let entries: Dirent[];
    try {
      entries = await fs.readdir(dir, { withFileTypes: true });
    } catch {
      continue; // Directory may not exist yet — skip
    }

    for (const entry of entries) {
      if (!entry.isFile()) continue;
      const name = entry.name;
      if (!name.endsWith('.yml') && !name.endsWith('.yaml')) continue;

      try {
        const raw = await fs.readFile(path.join(dir, name), 'utf-8');
        const doc = yaml.load(raw);
        if (doc && typeof doc === 'object') {
          results.push(doc as Record<string, unknown>);
        }
      } catch {
        // Malformed YAML — skip file gracefully (REQ-NFR-REL-001)
      }
    }
  }

  return results;
}

/**
 * Map a raw YAML document to a typed FeatureVector.
 * Fields that are missing are given safe defaults.
 */
function toFeatureVector(raw: Record<string, unknown>): FeatureVector {
  const trajectory: Record<string, { status: string; iteration: number }> = {};

  if (raw['trajectory'] && typeof raw['trajectory'] === 'object') {
    const rawTraj = raw['trajectory'] as Record<string, unknown>;
    for (const [edge, val] of Object.entries(rawTraj)) {
      if (val && typeof val === 'object') {
        const edgeVal = val as Record<string, unknown>;
        trajectory[edge] = {
          status: typeof edgeVal['status'] === 'string' ? edgeVal['status'] : 'pending',
          iteration: typeof edgeVal['iteration'] === 'number' ? edgeVal['iteration'] : 0,
        };
      }
    }
  }

  const satisfies: string[] = Array.isArray(raw['satisfies'])
    ? (raw['satisfies'] as unknown[]).filter((s) => typeof s === 'string') as string[]
    : [];

  const childVectors: string[] = Array.isArray(raw['children'])
    ? (raw['children'] as unknown[])
        .filter((c) => c && typeof c === 'object' && typeof (c as Record<string, unknown>)['feature'] === 'string')
        .map((c) => (c as Record<string, unknown>)['feature'] as string)
    : [];

  return {
    // featureId — client-facing name; raw YAML field is 'feature'
    featureId: typeof raw['feature'] === 'string' ? raw['feature'] : 'unknown',
    // Keep internal field for server-side lookups
    feature: typeof raw['feature'] === 'string' ? raw['feature'] : 'unknown',
    title: typeof raw['title'] === 'string' ? raw['title'] : '',
    status: typeof raw['status'] === 'string' ? raw['status'] : 'pending',
    trajectory,
    satisfies,
    childVectors,
    // Derived from events — set by getFeatures() after event scan
    currentEdge: null,
    currentDelta: null,
    autoModeEnabled: false,
  };
}

/**
 * Derive the list of pending GateItems from events.jsonl.
 *
 * A gate is pending when there is a `review_requested` event for a
 * feature+edge+gate_name that has no following `review_approved` or
 * `review_rejected` event for the same triple.
 */
function derivePendingGates(
  events: WorkspaceEvent[],
): GateItem[] {
  // Build set of resolved gates: feature:edge:gate_name
  const resolved = new Set<string>();
  for (const ev of events) {
    if (ev.event_type === 'review_approved' || ev.event_type === 'review_rejected') {
      const feature = ev.feature ?? '';
      const edge = ev.edge ?? '';
      const gateName = (ev['gate_name'] as string | undefined) ?? '';
      resolved.add(`${feature}:${edge}:${gateName}`);
    }
  }

  const gates: GateItem[] = [];
  for (const ev of events) {
    if (ev.event_type !== 'review_requested') continue;
    const feature = ev.feature ?? '';
    const edge = ev.edge ?? '';
    const gateName = (ev['gate_name'] as string | undefined) ?? '';
    const key = `${feature}:${edge}:${gateName}`;
    if (!resolved.has(key)) {
      const isStuck = computeIsStuck(events, feature, edge);
      gates.push({
        id: key,
        feature,
        edge,
        requestedAt: ev.timestamp,
        isStuck,
      });
    }
  }

  return gates;
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Return a lightweight WorkspaceSummary for a registered workspace.
 * Used for the project list page polling.
 */
export async function getWorkspaceSummary(
  workspacePath: string,
  workspaceId: string,
): Promise<WorkspaceSummary> {
  const eventsPath = path.join(workspacePath, 'events', 'events.jsonl');
  const { events } = await readAll(eventsPath);

  const pendingGates = derivePendingGates(events);

  // Count stuck features: for each active feature+edge, check isStuck
  let stuckFeatures = 0;
  const featureEdgeSeen = new Set<string>();
  for (const ev of events) {
    if (ev.event_type === 'iteration_completed' && ev.feature && ev.edge) {
      const key = `${ev.feature}:${ev.edge}`;
      if (!featureEdgeSeen.has(key)) {
        featureEdgeSeen.add(key);
        if (computeIsStuck(events, ev.feature, ev.edge)) {
          stuckFeatures++;
        }
      }
    }
  }

  const lastEventAt =
    events.length > 0 ? events[events.length - 1].timestamp : null;

  const name = await readProjectName(workspacePath);

  return {
    workspaceId,
    projectName: name,
    activeFeatureCount: 0, // derived from feature vectors if needed
    pendingGateCount: pendingGates.length,
    stuckFeatureCount: stuckFeatures,
    lastEventTimestamp: lastEventAt,
    hasAttentionRequired: pendingGates.length > 0 || stuckFeatures > 0,
    available: true,
  };
}

/**
 * Return a WorkspaceOverview with computed status counts, in-progress features,
 * and recent activity — shaped to match the client's WorkspaceOverview interface.
 */
export async function getOverview(
  workspacePath: string,
  workspaceId: string,
): Promise<WorkspaceOverview> {
  const eventsPath = path.join(workspacePath, 'events', 'events.jsonl');
  const { events } = await readAll(eventsPath);

  const rawFeatures = await readFeatureYamls(workspacePath);
  const features = rawFeatures.map(toFeatureVector);
  const projectName = await readProjectName(workspacePath);
  const pendingGates = derivePendingGates(events);

  // ── Status counts ──────────────────────────────────────────────────────────
  const statusCounts = { converged: 0, in_progress: 0, blocked: 0, pending: 0, pendingGates: pendingGates.length };
  for (const f of features) {
    const s = f.status;
    if (s === 'converged') statusCounts.converged++;
    else if (s === 'in_progress' || s === 'iterating') statusCounts.in_progress++;
    else if (s === 'blocked') statusCounts.blocked++;
    else statusCounts.pending++;
  }

  // ── In-progress features ───────────────────────────────────────────────────
  // Build per-feature last-event timestamps and latest delta from events
  const featureLastEvents: Record<string, string> = {};
  const featureDelta: Record<string, number> = {};
  const featureEdge: Record<string, string> = {};
  const featureIter: Record<string, number> = {};
  for (const ev of events) {
    const fid = ev.feature;
    if (!fid) continue;
    featureLastEvents[fid] = ev.timestamp;
    if (ev.event_type === 'iteration_completed') {
      featureDelta[fid] = typeof ev['delta'] === 'number' ? (ev['delta'] as number) : 0;
      featureEdge[fid] = ev.edge ?? '';
      featureIter[fid] = typeof ev['iteration'] === 'number' ? (ev['iteration'] as number) : 0;
    }
    if (ev.event_type === 'edge_converged') {
      featureDelta[fid] = 0;
    }
  }

  const inProgressFeatures: InProgressFeature[] = features
    .filter((f) => f.status !== 'converged' && f.status !== 'pending')
    .map((f) => ({
      featureId: f.feature,
      title: f.title,
      currentEdge: featureEdge[f.feature] ?? '',
      iterationNumber: featureIter[f.feature] ?? 0,
      delta: featureDelta[f.feature] ?? 0,
      lastEventAt: featureLastEvents[f.feature] ?? new Date().toISOString(),
    }));

  // ── Recent activities — last 5 iteration_completed events ─────────────────
  const featureTitleMap: Record<string, string> = {};
  for (const f of features) { featureTitleMap[f.feature] = f.title; }

  const recentActivities: RecentActivity[] = [];
  for (let i = events.length - 1; i >= 0 && recentActivities.length < 5; i--) {
    const ev = events[i];
    if (ev.event_type === 'iteration_completed' && ev.feature && ev.edge) {
      recentActivities.push({
        featureId: ev.feature,
        title: featureTitleMap[ev.feature] ?? ev.feature,
        edge: ev.edge,
        iterationNumber: typeof ev['iteration'] === 'number' ? (ev['iteration'] as number) : 0,
        timestamp: ev.timestamp,
        delta: typeof ev['delta'] === 'number' ? (ev['delta'] as number) : 0,
        runId: typeof ev['run_id'] === 'string' ? (ev['run_id'] as string) : null,
      });
    }
  }

  const blockedFeatures: BlockedFeatureSummary[] = features
    .filter((f) => f.status === 'blocked')
    .map((f) => ({
      featureId: f.feature,
      title: f.title,
      reason: null,
    }));

  return {
    projectName,
    methodVersion: 'v2.9',
    statusCounts,
    inProgressFeatures,
    recentActivities,
    featureLastEvents,
    pendingGateCount: pendingGates.length,
    pendingGates,
    blockedFeatures,
  };
}

/**
 * Return all currently pending human gate items for the workspace.
 */
export async function getGates(workspacePath: string): Promise<GateItem[]> {
  const eventsPath = path.join(workspacePath, 'events', 'events.jsonl');
  const { events } = await readAll(eventsPath);
  return derivePendingGates(events);
}

/**
 * Return all feature vectors (active + completed) for the workspace.
 * currentEdge, currentDelta, and autoModeEnabled are derived from events.
 */
export async function getFeatures(
  workspacePath: string,
): Promise<FeatureVector[]> {
  const rawFeatures = await readFeatureYamls(workspacePath);
  const features = rawFeatures.map(toFeatureVector);

  // Derive event-based fields from the event log
  const eventsPath = path.join(workspacePath, 'events', 'events.jsonl');
  const { events } = await readAll(eventsPath);

  for (const f of features) {
    // currentEdge + currentDelta: last iteration_completed for this feature
    for (let i = events.length - 1; i >= 0; i--) {
      const ev = events[i];
      if (ev.feature === f.feature && ev.event_type === 'iteration_completed' && ev.edge) {
        f.currentEdge = ev.edge;
        f.currentDelta = typeof ev['delta'] === 'number' ? (ev['delta'] as number) : null;
        break;
      }
    }
    // Reset delta to 0 if the edge then converged
    for (let i = events.length - 1; i >= 0; i--) {
      const ev = events[i];
      if (ev.feature === f.feature && ev.event_type === 'edge_converged') {
        if (ev.edge === f.currentEdge) f.currentDelta = 0;
        break;
      }
    }
    // autoModeEnabled: most recent auto_mode_set event
    f.autoModeEnabled = computeAutoMode(events, f.feature);
  }

  return features;
}

// ---------------------------------------------------------------------------
// Feature detail
// ---------------------------------------------------------------------------

export interface IterationSummary {
  iteration: number;
  timestamp: string;
  delta: number | null;
  status: string;
  evaluatorsPassed: number;
  evaluatorsFailed: number;
  evaluatorsSkipped: number;
  evaluatorsTotal: number;
}

export interface FeatureEdgeStatus {
  edge: string;
  status: string;
  iterationCount: number;
  delta: number | null;
  lastRunId: string | null;
  convergedAt: string | null;
  producedAsset: string | null;
  iterations: IterationSummary[];
}

export interface FeatureEventSummary {
  eventIndex: number;
  eventType: string;
  timestamp: string;
  edge: string | null;
  iteration: number | null;
  delta: number | null;
  runId: string | null;
  raw: Record<string, unknown>;
}

export interface FeatureDetail {
  featureId: string;
  title: string;
  description: string;
  intent: string;
  profile: string;
  vectorType: string;
  status: string;
  currentEdge: string | null;
  currentDelta: number | null;
  satisfies: string[];
  childVectors: string[];
  edges: FeatureEdgeStatus[];
  events: FeatureEventSummary[];
}

/**
 * Return a rich feature detail for a single feature, including trajectory
 * and recent events filtered to this feature.
 * Implements: REQ-F-NAV-003
 */
export async function getFeatureDetail(
  workspacePath: string,
  featureId: string,
): Promise<FeatureDetail | null> {
  const rawFeatures = await readFeatureYamls(workspacePath);
  const raw = rawFeatures.find((r) => r['feature'] === featureId);
  if (!raw) return null;

  // ── Events for this feature ───────────────────────────────────────────────
  const eventsPath = path.join(workspacePath, 'events', 'events.jsonl');
  const { events: allEvents } = await readAll(eventsPath);
  const featureEvents = allEvents
    .map((ev, idx) => ({ ev, globalIndex: idx }))
    .filter(({ ev }) => ev.feature === featureId);

  // Build per-edge last delta, runId, and per-iteration summaries from events
  const edgeDelta: Record<string, number | null> = {};
  const edgeRunId: Record<string, string | null> = {};
  const edgeIterations: Record<string, IterationSummary[]> = {};
  for (const { ev } of featureEvents) {
    if (ev.event_type === 'iteration_completed' && ev.edge) {
      edgeDelta[ev.edge] = typeof ev['delta'] === 'number' ? (ev['delta'] as number) : null;
      edgeRunId[ev.edge] = typeof ev['run_id'] === 'string' ? (ev['run_id'] as string) : null;
      const evalData = ev['evaluators'] as Record<string, unknown> | undefined;
      const iter: IterationSummary = {
        iteration: typeof ev['iteration'] === 'number' ? (ev['iteration'] as number) : 0,
        timestamp: ev.timestamp,
        delta: typeof ev['delta'] === 'number' ? (ev['delta'] as number) : null,
        status: typeof ev['status'] === 'string' ? (ev['status'] as string) : 'iterating',
        evaluatorsPassed: typeof evalData?.['passed'] === 'number' ? (evalData['passed'] as number) : 0,
        evaluatorsFailed: typeof evalData?.['failed'] === 'number' ? (evalData['failed'] as number) : 0,
        evaluatorsSkipped: typeof evalData?.['skipped'] === 'number' ? (evalData['skipped'] as number) : 0,
        evaluatorsTotal: typeof evalData?.['total'] === 'number' ? (evalData['total'] as number) : 0,
      };
      if (!edgeIterations[ev.edge]) edgeIterations[ev.edge] = [];
      edgeIterations[ev.edge].push(iter);
    }
    if (ev.event_type === 'edge_converged' && ev.edge) {
      edgeDelta[ev.edge] = 0;
    }
  }

  // ── Trajectory edges ─────────────────────────────────────────────────────
  const edges: FeatureEdgeStatus[] = [];
  if (raw['trajectory'] && typeof raw['trajectory'] === 'object') {
    const traj = raw['trajectory'] as Record<string, unknown>;
    for (const [edgeName, val] of Object.entries(traj)) {
      if (val && typeof val === 'object') {
        const e = val as Record<string, unknown>;
        edges.push({
          edge: edgeName,
          status: typeof e['status'] === 'string' ? e['status'] : 'pending',
          iterationCount: typeof e['iteration'] === 'number' ? (e['iteration'] as number) : 0,
          delta: edgeDelta[edgeName] ?? null,
          lastRunId: edgeRunId[edgeName] ?? null,
          convergedAt: typeof e['converged_at'] === 'string' ? (e['converged_at'] as string) : null,
          producedAsset: typeof e['produced_asset_ref'] === 'string' ? (e['produced_asset_ref'] as string) : null,
          iterations: edgeIterations[edgeName] ?? [],
        });
      }
    }
  }

  // ── Derive current edge and delta ─────────────────────────────────────────
  const inProgressEdge = edges.find((e) => e.status !== 'converged' && e.status !== 'pending');
  let currentEdge: string | null = inProgressEdge?.edge ?? null;
  let currentDelta: number | null = inProgressEdge?.delta ?? null;
  if (!currentEdge) {
    // Derive from events
    for (let i = allEvents.length - 1; i >= 0; i--) {
      const ev = allEvents[i];
      if (ev.feature === featureId && ev.event_type === 'iteration_completed' && ev.edge) {
        currentEdge = ev.edge;
        currentDelta = typeof ev['delta'] === 'number' ? (ev['delta'] as number) : null;
        break;
      }
    }
  }

  // ── Recent events (last 50, in chronological order) ──────────────────────
  const recentEvents: FeatureEventSummary[] = featureEvents.slice(-50).map(({ ev, globalIndex }) => ({
    eventIndex: globalIndex,
    eventType: ev.event_type,
    timestamp: ev.timestamp,
    edge: ev.edge ?? null,
    iteration: typeof ev['iteration'] === 'number' ? (ev['iteration'] as number) : null,
    delta: typeof ev['delta'] === 'number' ? (ev['delta'] as number) : null,
    runId: typeof ev['run_id'] === 'string' ? (ev['run_id'] as string) : null,
    raw: ev as unknown as Record<string, unknown>,
  }));

  // ── Satisfies ─────────────────────────────────────────────────────────────
  const satisfies: string[] = Array.isArray(raw['satisfies'])
    ? (raw['satisfies'] as unknown[]).filter((s) => typeof s === 'string') as string[]
    : [];

  // ── Children ──────────────────────────────────────────────────────────────
  const childVectors: string[] = Array.isArray(raw['children'])
    ? (raw['children'] as unknown[])
        .filter((c) => c && typeof c === 'object' && typeof (c as Record<string, unknown>)['feature'] === 'string')
        .map((c) => (c as Record<string, unknown>)['feature'] as string)
    : [];

  return {
    featureId,
    title: typeof raw['title'] === 'string' ? raw['title'] : '',
    description: typeof raw['description'] === 'string' ? raw['description'] : '',
    intent: typeof raw['intent'] === 'string' ? raw['intent'] : '',
    profile: typeof raw['profile'] === 'string' ? raw['profile'] : '',
    vectorType: typeof raw['vector_type'] === 'string' ? raw['vector_type'] : 'feature',
    status: typeof raw['status'] === 'string' ? raw['status'] : 'pending',
    currentEdge,
    currentDelta,
    satisfies,
    childVectors,
    edges,
    events: recentEvents,
  };
}
