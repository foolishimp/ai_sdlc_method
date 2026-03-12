// Implements: REQ-DATA-WORK-002, ADR-GM-005
// Acquires a proper-lockfile lock on events.jsonl, constructs the full event
// JSON (adding timestamp and project name from project_constraints.yml),
// appends a single JSONL line, releases the lock, then calls WriteLog.

import fs from 'node:fs/promises';
import path from 'node:path';
import lockfile from 'proper-lockfile';
import yaml from 'js-yaml';
import { WriteError } from '../types.js';
import { appendWriteLog } from './WriteLog.js';
import type { EventPayloadIn } from '../types.js';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Read the project name from .ai-workspace/project_constraints.yml.
 * Returns "unknown" if the file is absent or malformed.
 */
async function readProjectName(workspacePath: string): Promise<string> {
  const constraintsPath = path.join(
    workspacePath,
    'project_constraints.yml',
  );
  try {
    const raw = await fs.readFile(constraintsPath, 'utf-8');
    const doc = yaml.load(raw) as Record<string, unknown> | null;
    if (doc && typeof doc['project_name'] === 'string') {
      return doc['project_name'];
    }
    if (doc && typeof doc['name'] === 'string') {
      return doc['name'];
    }
    return 'unknown';
  } catch {
    return 'unknown';
  }
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Emit a single event to events.jsonl using a file lock (proper-lockfile).
 *
 * The full event JSON is constructed here — the client never supplies the
 * timestamp or project fields. This ensures the event log remains
 * internally consistent even if multiple browser tabs fire simultaneously.
 *
 * Throws WriteError on lock failure or IO error.
 */
export async function emitEvent(
  workspacePath: string,
  payload: EventPayloadIn,
): Promise<void> {
  if (!payload.event_type || typeof payload.event_type !== 'string') {
    throw new WriteError('event_type is required', 'INVALID_PAYLOAD');
  }

  const eventsPath = path.join(workspacePath, 'events', 'events.jsonl');

  // Ensure the events file exists before attempting to lock it
  try {
    await fs.access(eventsPath);
  } catch {
    throw new WriteError(
      `events.jsonl not found at ${eventsPath}`,
      'IO_ERROR',
    );
  }

  const projectName = await readProjectName(workspacePath);

  const fullEvent: Record<string, unknown> = {
    event_type: payload.event_type,
    timestamp: new Date().toISOString(),
    project: projectName,
    ...(payload.feature !== undefined && { feature: payload.feature }),
    ...(payload.edge !== undefined && { edge: payload.edge }),
    ...(payload.actor !== undefined && { actor: payload.actor }),
    ...(payload.comment !== undefined && { comment: payload.comment }),
    ...(payload.data !== undefined && { data: payload.data }),
  };

  let release: (() => Promise<void>) | null = null;

  try {
    release = await lockfile.lock(eventsPath, {
      retries: { retries: 5, minTimeout: 50, maxTimeout: 200 },
      stale: 10000,
    });
  } catch (err) {
    throw new WriteError(
      `Failed to acquire lock on events.jsonl: ${String(err)}`,
      'LOCK_TIMEOUT',
    );
  }

  try {
    const line = JSON.stringify(fullEvent) + '\n';
    await fs.appendFile(eventsPath, line, 'utf-8');
  } catch (err) {
    throw new WriteError(
      `Failed to append event to events.jsonl: ${String(err)}`,
      'IO_ERROR',
    );
  } finally {
    if (release) {
      await release();
    }
  }

  // Audit trail — best-effort, non-fatal
  await appendWriteLog({
    timestamp: fullEvent['timestamp'] as string,
    action: 'emit_event',
    workspacePath,
    eventType: payload.event_type,
    actor: payload.actor,
  });
}
