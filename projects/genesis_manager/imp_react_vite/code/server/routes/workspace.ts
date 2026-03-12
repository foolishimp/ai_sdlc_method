// Implements: REQ-F-OVR-001, REQ-F-SUP-001, REQ-F-EVI-001
// Express Router for workspace detail endpoints.
// GET /api/workspaces/:id/overview      — WorkspaceOverview
// GET /api/workspaces/:id/gates         — GateItem[]
// GET /api/workspaces/:id/features      — FeatureVector[]
// GET /api/workspaces/:id/traceability  — TraceabilityEntry[]

import { Router, Request, Response } from 'express';
import path from 'node:path';
import {
  loadRegistry,
  findById,
} from '../lib/workspaceRegistry.js';
import {
  getOverview,
  getGates,
  getFeatures,
} from '../readers/WorkspaceReader.js';
import { scan } from '../readers/TraceabilityScanner.js';

const router = Router();

// ---------------------------------------------------------------------------
// Shared helper: resolve workspace path from id or return 404
// ---------------------------------------------------------------------------

async function resolveWorkspacePath(
  id: string,
  res: Response,
): Promise<string | null> {
  const registry = await loadRegistry();
  const reg = findById(id, registry);
  if (!reg) {
    res.status(404).json({ message: 'workspace not found' });
    return null;
  }
  return reg.path;
}

// ---------------------------------------------------------------------------
// GET /api/workspaces/:id/overview
// ---------------------------------------------------------------------------

router.get('/:id/overview', async (req: Request, res: Response): Promise<void> => {
  const id = req.params['id'] as string;
  try {
    const workspacePath = await resolveWorkspacePath(id, res);
    if (!workspacePath) return;

    const overview = await getOverview(workspacePath, id);
    res.json(overview);
  } catch (err) {
    console.error('[GET /workspaces/:id/overview]', err);
    res.status(500).json({ message: 'Failed to load workspace overview' });
  }
});

// ---------------------------------------------------------------------------
// GET /api/workspaces/:id/gates
// ---------------------------------------------------------------------------

router.get('/:id/gates', async (req: Request, res: Response): Promise<void> => {
  const id = req.params['id'] as string;
  try {
    const workspacePath = await resolveWorkspacePath(id, res);
    if (!workspacePath) return;

    const gates = await getGates(workspacePath);
    res.json(gates);
  } catch (err) {
    console.error('[GET /workspaces/:id/gates]', err);
    res.status(500).json({ message: 'Failed to load workspace gates' });
  }
});

// ---------------------------------------------------------------------------
// GET /api/workspaces/:id/features
// ---------------------------------------------------------------------------

router.get('/:id/features', async (req: Request, res: Response): Promise<void> => {
  const id = req.params['id'] as string;
  try {
    const workspacePath = await resolveWorkspacePath(id, res);
    if (!workspacePath) return;

    const features = await getFeatures(workspacePath);
    res.json(features);
  } catch (err) {
    console.error('[GET /workspaces/:id/features]', err);
    res.status(500).json({ message: 'Failed to load workspace features' });
  }
});

// ---------------------------------------------------------------------------
// GET /api/workspaces/:id/traceability
// Project root = parent of the .ai-workspace/ directory.
// (consistent with how gen-gaps resolves the project root — REQ-F-EVI-001)
// ---------------------------------------------------------------------------

router.get('/:id/traceability', async (req: Request, res: Response): Promise<void> => {
  const id = req.params['id'] as string;
  try {
    const workspacePath = await resolveWorkspacePath(id, res);
    if (!workspacePath) return;

    // workspacePath IS the .ai-workspace/ directory; project root is its parent
    const projectRoot = path.dirname(workspacePath);
    const entries = await scan(projectRoot);
    res.json(entries);
  } catch (err) {
    console.error('[GET /workspaces/:id/traceability]', err);
    res.status(500).json({ message: 'Failed to scan traceability' });
  }
});

export default router;
