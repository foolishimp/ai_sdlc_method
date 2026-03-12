// Implements: REQ-DATA-WORK-002, ADR-GM-005
// Express Router for the workspace event write path.
// POST /api/workspaces/:id/events — append a validated event to events.jsonl

import { Router, Request, Response } from 'express';
import {
  loadRegistry,
  findById,
} from '../lib/workspaceRegistry.js';
import { emitEvent } from '../handlers/EventEmitHandler.js';
import { WriteError } from '../types.js';
import type { EventPayloadIn } from '../types.js';

const router = Router();

// ---------------------------------------------------------------------------
// POST /api/workspaces/:id/events
// Body: EventPayloadIn (event_type required; feature, edge, actor, comment, data optional)
// 200 → success
// 400 → invalid payload
// 503 → lock acquisition failed (try again)
// ---------------------------------------------------------------------------

router.post('/:id/events', async (req: Request, res: Response): Promise<void> => {
  const id = req.params['id'] as string;

  try {
    const registry = await loadRegistry();
    const reg = findById(id, registry);

    if (!reg) {
      res.status(404).json({ message: 'workspace not found' });
      return;
    }

    const body = req.body as Partial<EventPayloadIn>;

    if (!body.event_type || typeof body.event_type !== 'string') {
      res.status(400).json({ message: 'event_type is required' });
      return;
    }

    const payload: EventPayloadIn = {
      event_type: body.event_type,
      ...(body.feature !== undefined && { feature: body.feature }),
      ...(body.edge !== undefined && { edge: body.edge }),
      ...(body.actor !== undefined && { actor: body.actor }),
      ...(body.comment !== undefined && { comment: body.comment }),
      ...(body.data !== undefined && { data: body.data }),
    };

    await emitEvent(reg.path, payload);

    res.status(200).json({ ok: true });
  } catch (err) {
    if (err instanceof WriteError) {
      if (err.code === 'LOCK_TIMEOUT') {
        res.status(503).json({
          message: 'events.jsonl is locked by another writer — retry',
          code: err.code,
        });
        return;
      }
      if (err.code === 'INVALID_PAYLOAD') {
        res.status(400).json({ message: err.message, code: err.code });
        return;
      }
      res.status(500).json({ message: err.message, code: err.code });
      return;
    }
    console.error('[POST /events/:id/events]', err);
    res.status(500).json({ message: 'Unexpected error emitting event' });
  }
});

export default router;
