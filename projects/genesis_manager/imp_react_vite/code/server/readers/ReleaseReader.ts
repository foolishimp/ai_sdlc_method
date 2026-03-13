// Implements: REQ-F-REL-001, REQ-F-REL-002, REQ-F-REL-003
// Reads Genesis workspace artifacts to compute release readiness, release scope,
// and to initiate a release by appending a release_created event.

import fs from 'node:fs/promises';
import { Dirent } from 'node:fs';
import path from 'node:path';
import yaml from 'js-yaml';
import { readAll } from './EventLogReader.js';
import type {
  ReleaseReadiness,
  ReadinessCondition,
  ReleaseScopeItem,
  ReleaseResult,
  WorkspaceEvent,
} from '../types.js';

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

/**
 * Read all YAML files from a single directory, returning parsed documents.
 */
async function readYamlsFromDir(
  dir: string,
): Promise<Array<Record<string, unknown>>> {
  let entries: Dirent[];
  try {
    entries = await fs.readdir(dir, { withFileTypes: true });
  } catch {
    return []; // Directory may not exist yet — skip
  }

  const results: Array<Record<string, unknown>> = [];
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
  return results;
}

/**
 * Derive pending gates from events:
 * A gate is pending when there is a review_requested with no following
 * review_approved or review_rejected for the same feature:edge:gate_name triple.
 */
function hasPendingGates(events: WorkspaceEvent[]): boolean {
  const resolved = new Set<string>();
  for (const ev of events) {
    if (ev.event_type === 'review_approved' || ev.event_type === 'review_rejected') {
      const feature = ev.feature ?? '';
      const edge = ev.edge ?? '';
      const gateName = (ev['gate_name'] as string | undefined) ?? '';
      resolved.add(`${feature}:${edge}:${gateName}`);
    }
  }
  for (const ev of events) {
    if (ev.event_type !== 'review_requested') continue;
    const feature = ev.feature ?? '';
    const edge = ev.edge ?? '';
    const gateName = (ev['gate_name'] as string | undefined) ?? '';
    const key = `${feature}:${edge}:${gateName}`;
    if (!resolved.has(key)) return true;
  }
  return false;
}

/**
 * Check if the last gaps_validated event has both layer_1 and layer_2 passing.
 */
function gapsValidatedPass(events: WorkspaceEvent[]): boolean {
  for (let i = events.length - 1; i >= 0; i--) {
    const ev = events[i];
    if (ev.event_type === 'gaps_validated') {
      const data = (ev['data'] ?? ev) as Record<string, unknown>;
      const layerResults = data['layer_results'] as Record<string, unknown> | undefined;
      if (!layerResults) return false;
      const l1 = layerResults['layer_1'];
      const l2 = layerResults['layer_2'];
      return (
        (l1 === 'pass' || l1 === 'PASS') &&
        (l2 === 'pass' || l2 === 'PASS')
      );
    }
  }
  return false; // No gaps_validated event found
}

/**
 * Extract converged and pending edge lists from a feature vector YAML document.
 */
function extractEdgeLists(raw: Record<string, unknown>): {
  convergedEdges: string[];
  pendingEdges: string[];
} {
  const convergedEdges: string[] = [];
  const pendingEdges: string[] = [];

  if (raw['trajectory'] && typeof raw['trajectory'] === 'object') {
    const traj = raw['trajectory'] as Record<string, unknown>;
    for (const [edgeName, val] of Object.entries(traj)) {
      if (val && typeof val === 'object') {
        const edgeVal = val as Record<string, unknown>;
        const status = typeof edgeVal['status'] === 'string' ? edgeVal['status'] : 'pending';
        if (status === 'converged') {
          convergedEdges.push(edgeName);
        } else {
          pendingEdges.push(edgeName);
        }
      }
    }
  }

  return { convergedEdges, pendingEdges };
}

/**
 * Compute REQ key coverage percentage for a feature.
 * Returns the count of satisfies keys as a proxy for coverage % (0-100).
 * If no satisfies keys exist, returns 0.
 */
function computeCoveragePct(raw: Record<string, unknown>): number {
  const satisfies: string[] = Array.isArray(raw['satisfies'])
    ? (raw['satisfies'] as unknown[]).filter((s) => typeof s === 'string') as string[]
    : [];
  // Coverage % = satisfies count relative to edges (proxy metric)
  // We report 100% if converged, proportional otherwise
  const status = typeof raw['status'] === 'string' ? raw['status'] : 'pending';
  if (status === 'converged') return satisfies.length > 0 ? 100 : 0;
  const { convergedEdges, pendingEdges } = extractEdgeLists(raw);
  const total = convergedEdges.length + pendingEdges.length;
  if (total === 0) return 0;
  return Math.round((convergedEdges.length / total) * 100);
}

/**
 * Suggest next version by reading the last release_created event and bumping patch.
 */
export async function suggestNextVersion(eventsPath: string): Promise<string> {
  const { events } = await readAll(eventsPath);
  for (let i = events.length - 1; i >= 0; i--) {
    const ev = events[i];
    if (ev.event_type === 'release_created') {
      const version = (ev['version'] as string | undefined) ??
        ((ev['data'] as Record<string, unknown> | undefined)?.['version'] as string | undefined);
      if (version && /^\d+\.\d+\.\d+$/.test(version)) {
        const parts = version.split('.').map(Number);
        parts[2] = (parts[2] ?? 0) + 1;
        return parts.join('.');
      }
    }
  }
  return '1.0.0';
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Compute release readiness for a workspace.
 * Implements: REQ-F-REL-001
 *
 * Checks three conditions:
 *   1. all_features_converged — active features dir is empty (or all YMLs have status=converged)
 *   2. no_pending_gates       — no unresolved review_requested events
 *   3. gaps_validated         — last gaps_validated event has layer_1/layer_2 = 'pass'
 */
export async function computeReadiness(
  workspacePath: string,
  eventsPath: string,
): Promise<ReleaseReadiness> {
  const { events } = await readAll(eventsPath);

  // Condition 1: all active features converged
  const activeDir = path.join(workspacePath, 'features', 'active');
  const activeFeatures = await readYamlsFromDir(activeDir);
  const allConverged = activeFeatures.every((f) => {
    const status = typeof f['status'] === 'string' ? f['status'] : 'pending';
    return status === 'converged';
  });
  const activePassed = activeFeatures.length === 0 || allConverged;

  // Condition 2: no pending human gates
  const noPendingGates = !hasPendingGates(events);

  // Condition 3: gaps_validated L1 + L2 pass
  const gapsPassed = gapsValidatedPass(events);

  const conditions: ReadinessCondition[] = [
    {
      id: 'all_features_converged',
      label: 'All active features converged',
      passed: activePassed,
      link: 'supervision',
    },
    {
      id: 'no_pending_gates',
      label: 'No pending human gates',
      passed: noPendingGates,
      link: 'supervision',
    },
    {
      id: 'gaps_validated',
      label: 'Gap analysis L1 + L2 PASS',
      passed: gapsPassed,
      link: 'evidence',
    },
  ];

  const verdict = conditions.every((c) => c.passed) ? 'ready' : 'not-ready';

  return { verdict, conditions };
}

/**
 * Return all features with their release scope status.
 * Implements: REQ-F-REL-002
 *
 * Converged features (from features/completed/) are eligible.
 * Active features (from features/active/) are in-progress.
 */
export async function getReleaseScopeFormatted(
  workspacePath: string,
): Promise<ReleaseScopeItem[]> {
  const completedDir = path.join(workspacePath, 'features', 'completed');
  const activeDir = path.join(workspacePath, 'features', 'active');

  const [completedRaw, activeRaw] = await Promise.all([
    readYamlsFromDir(completedDir),
    readYamlsFromDir(activeDir),
  ]);

  const items: ReleaseScopeItem[] = [];

  for (const raw of completedRaw) {
    const featureId = typeof raw['feature'] === 'string' ? raw['feature'] : 'unknown';
    const title = typeof raw['title'] === 'string' ? raw['title'] : featureId;
    const { convergedEdges, pendingEdges } = extractEdgeLists(raw);
    items.push({
      featureId,
      title,
      status: 'converged',
      coveragePct: 100,
      convergedEdges,
      pendingEdges,
    });
  }

  for (const raw of activeRaw) {
    const featureId = typeof raw['feature'] === 'string' ? raw['feature'] : 'unknown';
    const title = typeof raw['title'] === 'string' ? raw['title'] : featureId;
    const { convergedEdges, pendingEdges } = extractEdgeLists(raw);
    const coveragePct = computeCoveragePct(raw);
    items.push({
      featureId,
      title,
      status: 'in_progress',
      coveragePct,
      convergedEdges,
      pendingEdges,
    });
  }

  return items;
}

/**
 * Initiate a release by appending a release_created event to events.jsonl.
 * Implements: REQ-F-REL-003
 *
 * Does NOT run git — just emits the event.
 */
export async function initiateRelease(
  workspacePath: string,
  eventsPath: string,
  version: string,
): Promise<ReleaseResult> {
  const timestamp = new Date().toISOString();

  // Count converged features for the result
  const completedDir = path.join(workspacePath, 'features', 'completed');
  const completedRaw = await readYamlsFromDir(completedDir);
  const featuresIncluded = completedRaw.length;

  const event = {
    event_type: 'release_created',
    timestamp,
    version,
    actor: 'human',
    data: {
      features_included: featuresIncluded,
      method: 'genesis_manager_ui',
    },
  };

  const line = JSON.stringify(event) + '\n';
  await fs.appendFile(eventsPath, line, 'utf-8');

  return { version, timestamp, featuresIncluded };
}
