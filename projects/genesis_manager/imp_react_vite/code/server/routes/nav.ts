// Implements: REQ-F-NAV-001, REQ-F-NAV-002, REQ-F-NAV-003, REQ-F-NAV-004
// Navigation resolution endpoints — resolve feature IDs, REQ keys, and event
// indices to their underlying data for the NavHandle deep-link pattern.
//
// GET /api/features/:featureId?workspaceId=...  → FeatureVector
// GET /api/req/:reqKey?workspaceId=...          → events + traceability entries for this key
// GET /api/events/:eventIndex?workspaceId=...   → single event by 0-based line index

import { Router, Request, Response } from 'express';
import path from 'node:path';
import { loadRegistry, findById } from '../lib/workspaceRegistry.js';
import { getFeatures } from '../readers/WorkspaceReader.js';
import { readAll } from '../readers/EventLogReader.js';
import { scan } from '../readers/TraceabilityScanner.js';

const router = Router();

// ---------------------------------------------------------------------------
// Shared helper: resolve workspacePath from query param workspaceId
// ---------------------------------------------------------------------------

async function resolveWorkspaceFromQuery(
  query: Record<string, unknown>,
  res: Response,
): Promise<string | null> {
  const workspaceId = query['workspaceId'];
  if (typeof workspaceId !== 'string' || !workspaceId) {
    res.status(400).json({ message: 'workspaceId query parameter is required' });
    return null;
  }

  const registry = await loadRegistry();
  const reg = findById(workspaceId, registry);
  if (!reg) {
    res.status(404).json({ message: 'workspace not found' });
    return null;
  }
  return reg.path;
}

// ---------------------------------------------------------------------------
// GET /api/features/:featureId?workspaceId=...
// Returns the FeatureVector YAML for the given feature ID.
// ---------------------------------------------------------------------------

router.get('/features/:featureId', async (req: Request, res: Response): Promise<void> => {
  const featureId = req.params['featureId'] as string;

  try {
    const workspacePath = await resolveWorkspaceFromQuery(
      req.query as Record<string, unknown>,
      res,
    );
    if (!workspacePath) return;

    const features = await getFeatures(workspacePath);
    const feature = features.find((f) => f.feature === featureId);

    if (!feature) {
      res.status(404).json({ message: `Feature '${featureId}' not found` });
      return;
    }

    res.json(feature);
  } catch (err) {
    console.error('[GET /features/:featureId]', err);
    res.status(500).json({ message: 'Failed to resolve feature' });
  }
});

// ---------------------------------------------------------------------------
// GET /api/req/:reqKey?workspaceId=...
// Returns events that mention the REQ key + traceability entries for it.
// ---------------------------------------------------------------------------

router.get('/req/:reqKey', async (req: Request, res: Response): Promise<void> => {
  const reqKey = req.params['reqKey'] as string;

  try {
    const workspacePath = await resolveWorkspaceFromQuery(
      req.query as Record<string, unknown>,
      res,
    );
    if (!workspacePath) return;

    const eventsPath = path.join(workspacePath, 'events', 'events.jsonl');
    const { events } = await readAll(eventsPath);

    // Events that reference the REQ key anywhere in their stringified form
    const matchingEvents = events.filter((ev) => {
      const asString = JSON.stringify(ev);
      return asString.includes(reqKey);
    });

    // Traceability entries for this specific REQ key
    const projectRoot = path.dirname(workspacePath);
    const allEntries = await scan(projectRoot);
    const traceabilityEntries = allEntries.filter((e) => e.reqKey === reqKey);

    res.json({
      reqKey,
      events: matchingEvents,
      traceability: traceabilityEntries,
    });
  } catch (err) {
    console.error('[GET /req/:reqKey]', err);
    res.status(500).json({ message: 'Failed to resolve REQ key' });
  }
});

// ---------------------------------------------------------------------------
// GET /api/events/:eventIndex?workspaceId=...
// Returns the single event at the given 0-based line index in events.jsonl.
// Line indices are stable because events.jsonl is append-only (REQ-DATA-WORK-001).
// ---------------------------------------------------------------------------

router.get('/events/:eventIndex', async (req: Request, res: Response): Promise<void> => {
  const rawIndex = req.params['eventIndex'] as string;
  const eventIndex = parseInt(rawIndex, 10);

  if (isNaN(eventIndex) || eventIndex < 0) {
    res.status(400).json({ message: 'eventIndex must be a non-negative integer' });
    return;
  }

  try {
    const workspacePath = await resolveWorkspaceFromQuery(
      req.query as Record<string, unknown>,
      res,
    );
    if (!workspacePath) return;

    const eventsPath = path.join(workspacePath, 'events', 'events.jsonl');
    const { events } = await readAll(eventsPath);

    if (eventIndex >= events.length) {
      res.status(404).json({ message: `No event at index ${eventIndex}` });
      return;
    }

    res.json({ eventIndex, event: events[eventIndex] });
  } catch (err) {
    console.error('[GET /events/:eventIndex]', err);
    res.status(500).json({ message: 'Failed to resolve event' });
  }
});

export default router;
