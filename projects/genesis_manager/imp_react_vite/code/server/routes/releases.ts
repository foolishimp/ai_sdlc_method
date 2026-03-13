// Implements: REQ-F-REL-001, REQ-F-REL-002, REQ-F-REL-003
// Express Router for release management endpoints.
// GET  /api/workspaces/:id/release/readiness  — ReleaseReadiness
// GET  /api/workspaces/:id/release/scope      — ReleaseScopeItem[]
// POST /api/workspaces/:id/release/initiate   — ReleaseResult

import { Router, Request, Response } from 'express';
import path from 'node:path';
import {
  loadRegistry,
  findById,
} from '../lib/workspaceRegistry.js';
import {
  computeReadiness,
  getReleaseScopeFormatted,
  initiateRelease,
  suggestNextVersion,
} from '../readers/ReleaseReader.js';

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
// GET /api/workspaces/:id/release/readiness
// Implements: REQ-F-REL-001
// ---------------------------------------------------------------------------

router.get('/:id/release/readiness', async (req: Request, res: Response): Promise<void> => {
  const id = req.params['id'] as string;
  try {
    const workspacePath = await resolveWorkspacePath(id, res);
    if (!workspacePath) return;

    const eventsPath = path.join(workspacePath, 'events', 'events.jsonl');
    const readiness = await computeReadiness(workspacePath, eventsPath);
    res.json(readiness);
  } catch (err) {
    console.error('[GET /workspaces/:id/release/readiness]', err);
    res.status(500).json({ message: 'Failed to compute release readiness' });
  }
});

// ---------------------------------------------------------------------------
// GET /api/workspaces/:id/release/scope
// Implements: REQ-F-REL-002
// ---------------------------------------------------------------------------

router.get('/:id/release/scope', async (req: Request, res: Response): Promise<void> => {
  const id = req.params['id'] as string;
  try {
    const workspacePath = await resolveWorkspacePath(id, res);
    if (!workspacePath) return;

    const scope = await getReleaseScopeFormatted(workspacePath);
    res.json(scope);
  } catch (err) {
    console.error('[GET /workspaces/:id/release/scope]', err);
    res.status(500).json({ message: 'Failed to load release scope' });
  }
});

// ---------------------------------------------------------------------------
// POST /api/workspaces/:id/release/initiate
// Body: { version: string }
// Implements: REQ-F-REL-003
// ---------------------------------------------------------------------------

router.post('/:id/release/initiate', async (req: Request, res: Response): Promise<void> => {
  const id = req.params['id'] as string;
  const body = req.body as { version?: unknown };

  if (typeof body.version !== 'string' || !body.version.trim()) {
    res.status(400).json({ message: 'version is required and must be a non-empty string' });
    return;
  }

  const version = body.version.trim();

  try {
    const workspacePath = await resolveWorkspacePath(id, res);
    if (!workspacePath) return;

    const eventsPath = path.join(workspacePath, 'events', 'events.jsonl');
    const result = await initiateRelease(workspacePath, eventsPath, version);
    res.json(result);
  } catch (err) {
    console.error('[POST /workspaces/:id/release/initiate]', err);
    res.status(500).json({ message: 'Failed to initiate release' });
  }
});

// ---------------------------------------------------------------------------
// GET /api/workspaces/:id/release/suggest-version
// Returns the auto-suggested next version based on last release event.
// Implements: REQ-F-REL-003 (version auto-suggestion)
// ---------------------------------------------------------------------------

router.get('/:id/release/suggest-version', async (req: Request, res: Response): Promise<void> => {
  const id = req.params['id'] as string;
  try {
    const workspacePath = await resolveWorkspacePath(id, res);
    if (!workspacePath) return;

    const eventsPath = path.join(workspacePath, 'events', 'events.jsonl');
    const version = await suggestNextVersion(eventsPath);
    res.json({ version });
  } catch (err) {
    console.error('[GET /workspaces/:id/release/suggest-version]', err);
    res.status(500).json({ message: 'Failed to suggest version' });
  }
});

export default router;
