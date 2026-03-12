// Implements: REQ-F-SUP-004, REQ-F-CTL-004, REQ-NFR-REL-001
// Parses events.jsonl into typed WorkspaceEvent arrays and computes derived
// values (auto-mode state, stuck detection).

import fs from 'node:fs/promises';
import type { WorkspaceEvent } from '../types.js';

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export interface ReadAllResult {
  events: WorkspaceEvent[];
  warnings: string[];
}

/**
 * Read and parse every line of events.jsonl.
 * Malformed lines are skipped and included in the warnings array
 * (REQ-NFR-REL-001 — graceful degradation, never crash on bad data).
 */
export async function readAll(eventsPath: string): Promise<ReadAllResult> {
  const warnings: string[] = [];
  let raw: string;

  try {
    raw = await fs.readFile(eventsPath, 'utf-8');
  } catch (err: unknown) {
    const nodeErr = err as NodeJS.ErrnoException;
    if (nodeErr.code === 'ENOENT') {
      return { events: [], warnings: [] };
    }
    throw err;
  }

  const events: WorkspaceEvent[] = [];
  const lines = raw.split('\n');

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

    try {
      const parsed: unknown = JSON.parse(line);
      if (
        typeof parsed === 'object' &&
        parsed !== null &&
        'event_type' in parsed &&
        'timestamp' in parsed
      ) {
        events.push(parsed as WorkspaceEvent);
      } else {
        warnings.push(`Line ${i + 1}: missing required fields (event_type, timestamp)`);
      }
    } catch {
      warnings.push(`Line ${i + 1}: invalid JSON — skipped`);
    }
  }

  return { events, warnings };
}

/**
 * Determine the current auto-mode state for a feature by finding the most
 * recent `auto_mode_set` event for the given featureId.
 * Returns false if no such event exists.
 */
export function computeAutoMode(
  events: WorkspaceEvent[],
  featureId: string,
): boolean {
  // Scan in reverse to find the most recent matching event efficiently
  for (let i = events.length - 1; i >= 0; i--) {
    const ev = events[i];
    if (ev.event_type === 'auto_mode_set' && ev.feature === featureId) {
      const data = ev['data'] as Record<string, unknown> | undefined;
      if (data && typeof data['enabled'] === 'boolean') {
        return data['enabled'];
      }
    }
  }
  return false;
}

/**
 * Determine whether a feature+edge combination is stuck.
 * A feature is stuck when the most recent 3 `iteration_completed` events for
 * the same feature+edge all carry an identical `delta` value (REQ-F-SUP-004).
 */
export function computeIsStuck(
  events: WorkspaceEvent[],
  featureId: string,
  edge: string,
): boolean {
  const relevant = events.filter(
    (ev) =>
      ev.event_type === 'iteration_completed' &&
      ev.feature === featureId &&
      ev.edge === edge,
  );

  if (relevant.length < 3) return false;

  const last3 = relevant.slice(-3);
  const deltas = last3.map((ev) => ev['delta']);

  // All three deltas must be defined and identical
  if (deltas.some((d) => d === undefined || d === null)) return false;
  return deltas.every((d) => d === deltas[0]);
}
