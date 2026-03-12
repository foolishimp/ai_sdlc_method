// Implements: REQ-F-PROJ-004, REQ-DATA-WORK-001
// Express Router for workspace registration management.
// GET /api/workspaces      — list all registered workspaces with summaries
// POST /api/workspaces     — register a new workspace path
// DELETE /api/workspaces/:id — deregister a workspace
// GET /api/workspaces/:id/summary — single workspace summary

import { Router, Request, Response } from 'express';
import fs from 'node:fs/promises';
import path from 'node:path';
import {
  loadRegistry,
  saveRegistry,
  findById,
  generateWorkspaceId,
} from '../lib/workspaceRegistry.js';
import {
  getWorkspaceSummary,
} from '../readers/WorkspaceReader.js';
import type { WorkspaceSummary } from '../types.js';

const router = Router();

// ---------------------------------------------------------------------------
// GET /api/workspaces
// Returns a summary for every registered workspace. Paths that are no longer
// accessible return a partial summary with null sentinel values (REQ-NFR-REL-001).
// ---------------------------------------------------------------------------

router.get('/', async (_req: Request, res: Response): Promise<void> => {
  try {
    const registry = await loadRegistry();
    const summaries: WorkspaceSummary[] = [];

    for (const reg of registry) {
      try {
        const summary = await getWorkspaceSummary(reg.path, reg.id);
        summaries.push(summary);
      } catch {
        // Workspace path unavailable — return a degraded summary (REQ-F-PROJ-004)
        summaries.push({
          id: reg.id,
          path: reg.path,
          name: reg.name,
          pendingGates: 0,
          stuckFeatures: 0,
          lastEventAt: null,
        });
      }
    }

    res.json(summaries);
  } catch (err) {
    console.error('[GET /workspaces]', err);
    res.status(500).json({ message: 'Failed to load workspaces' });
  }
});

// ---------------------------------------------------------------------------
// POST /api/workspaces
// Body: { path: string }
// Validates that the path exists and contains .ai-workspace/events/events.jsonl.
// Generates a stable id from path SHA-256, stores to registry, returns summary.
// ---------------------------------------------------------------------------

router.post('/', async (req: Request, res: Response): Promise<void> => {
  const body = req.body as Record<string, unknown>;
  const workspacePath = body['path'];

  if (typeof workspacePath !== 'string' || !workspacePath.trim()) {
    res.status(400).json({ message: 'path is required' });
    return;
  }

  const normalised = workspacePath.trim();

  // Validate: directory must exist
  try {
    const stat = await fs.stat(normalised);
    if (!stat.isDirectory()) {
      res.status(400).json({ message: 'path must be a directory' });
      return;
    }
  } catch {
    res.status(400).json({ message: `path not found: ${normalised}` });
    return;
  }

  // Validate: must contain .ai-workspace/events/events.jsonl
  const eventsPath = path.join(normalised, 'events', 'events.jsonl');
  try {
    await fs.access(eventsPath);
  } catch {
    res.status(400).json({
      message: 'not a valid Genesis workspace (.ai-workspace/events/events.jsonl not found)',
    });
    return;
  }

  const id = generateWorkspaceId(normalised);

  const registry = await loadRegistry();

  // Idempotent: skip if already registered
  if (!findById(id, registry)) {
    registry.push({ id, path: normalised, name: path.basename(path.dirname(normalised)) });
    await saveRegistry(registry);
  }

  try {
    const summary = await getWorkspaceSummary(normalised, id);
    res.status(201).json(summary);
  } catch {
    res.status(201).json({
      id,
      path: normalised,
      name: path.basename(path.dirname(normalised)),
      pendingGates: 0,
      stuckFeatures: 0,
      lastEventAt: null,
    } satisfies WorkspaceSummary);
  }
});

// ---------------------------------------------------------------------------
// DELETE /api/workspaces/:id
// ---------------------------------------------------------------------------

router.delete('/:id', async (req: Request, res: Response): Promise<void> => {
  const id = req.params['id'] as string;

  try {
    const registry = await loadRegistry();
    const updated = registry.filter((r) => r.id !== id);

    if (updated.length === registry.length) {
      res.status(404).json({ message: 'workspace not found' });
      return;
    }

    await saveRegistry(updated);
    res.status(204).send();
  } catch (err) {
    console.error('[DELETE /workspaces/:id]', err);
    res.status(500).json({ message: 'Failed to remove workspace' });
  }
});

// ---------------------------------------------------------------------------
// GET /api/workspaces/:id/summary
// ---------------------------------------------------------------------------

router.get('/:id/summary', async (req: Request, res: Response): Promise<void> => {
  const id = req.params['id'] as string;

  try {
    const registry = await loadRegistry();
    const reg = findById(id, registry);

    if (!reg) {
      res.status(404).json({ message: 'workspace not found' });
      return;
    }

    const summary = await getWorkspaceSummary(reg.path, id);
    res.json(summary);
  } catch (err) {
    console.error('[GET /workspaces/:id/summary]', err);
    res.status(500).json({ message: 'Failed to read workspace summary' });
  }
});

export default router;
