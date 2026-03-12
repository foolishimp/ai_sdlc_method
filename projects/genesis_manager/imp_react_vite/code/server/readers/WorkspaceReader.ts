// Implements: REQ-F-PROJ-001, REQ-F-OVR-001, REQ-F-SUP-001, REQ-NFR-REL-001
// Reads Genesis workspace artifacts (project_constraints.yml, feature vectors,
// events.jsonl) and assembles typed summary / overview / gate / feature objects.

import fs from 'node:fs/promises';
import { Dirent } from 'node:fs';
import path from 'node:path';
import yaml from 'js-yaml';
import { readAll, computeIsStuck } from './EventLogReader.js';
import type {
  WorkspaceSummary,
  WorkspaceOverview,
  GateItem,
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

  return {
    feature: typeof raw['feature'] === 'string' ? raw['feature'] : 'unknown',
    title: typeof raw['title'] === 'string' ? raw['title'] : '',
    status: typeof raw['status'] === 'string' ? raw['status'] : 'pending',
    trajectory,
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

  // ── Recent activity — last iteration_completed event ──────────────────────
  let recentActivity: RecentActivity | null = null;
  for (let i = events.length - 1; i >= 0; i--) {
    const ev = events[i];
    if (ev.event_type === 'iteration_completed' && ev.feature && ev.edge) {
      recentActivity = {
        featureId: ev.feature,
        edge: ev.edge,
        iterationNumber: typeof ev['iteration'] === 'number' ? (ev['iteration'] as number) : 0,
        timestamp: ev.timestamp,
        delta: typeof ev['delta'] === 'number' ? (ev['delta'] as number) : 0,
        runId: typeof ev['run_id'] === 'string' ? (ev['run_id'] as string) : null,
      };
      break;
    }
  }

  return {
    projectName,
    methodVersion: 'v2.9',
    statusCounts,
    inProgressFeatures,
    recentActivity,
    featureLastEvents,
    pendingGateCount: pendingGates.length,
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
 */
export async function getFeatures(
  workspacePath: string,
): Promise<FeatureVector[]> {
  const rawFeatures = await readFeatureYamls(workspacePath);
  return rawFeatures.map(toFeatureVector);
}
